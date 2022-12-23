import dataclasses
import os
import pathlib
import typing

from python_sdk import _log

from . import _config_decoder
from . import _optional

_CONFIG_DOCUMENT_FILE_LINE_SEPARATOR = "\n"
_CONFIG_DOCUMENT_KEY_VALUE_SEPARATOR = "="


@dataclasses.dataclass(frozen=True)
class _EnvironmentVariables:
    pass


@dataclasses.dataclass(frozen=True)
class _LocalFile:
    filepath: typing.Union[str, pathlib.Path]


# TODO: aws-parameter-store document
# TODO: aws-secrets-manager-store document
_SOURCE_FROM_OPTIONS = ["ENVIRONMENT_VARIABLES", "LOCAL_FILE"]


def _get_config_source() -> typing.Union[_EnvironmentVariables, _LocalFile]:
    source_from = os.environ.get("PYTHON_SDK_CONFIG_SOURCE_FROM", "ENVIRONMENT_VARIABLES")
    if source_from not in _SOURCE_FROM_OPTIONS:
        raise NotImplementedError(
            f"PYTHON_SDK_CONFIG_SOURCE_FROM {source_from} not supported. Available options: {_SOURCE_FROM_OPTIONS}"
        )

    source_from_local_file_filepath = os.environ.get("PYTHON_SDK_CONFIG_SOURCE_FROM_LOCAL_FILE_FILEPATH")
    if source_from == "LOCAL_FILE" and not source_from_local_file_filepath:
        raise ValueError(
            "PYTHON_SDK_CONFIG_SOURCE_FROM_LOCAL_FILE_FILEPATH is required when CONFIG_SOURCE_FROM is set to "
            "LOCAL_FILE"
        )

    if source_from == "ENVIRONMENT_VARIABLES":
        source_from = _EnvironmentVariables()
    elif source_from == "LOCAL_FILE":
        source_from = _LocalFile(filepath=source_from_local_file_filepath)
    else:
        # this should never happen
        raise AssertionError(f"PYTHON_SDK_CONFIG_SOURCE_FROM {source_from} not implemented.")

    _log.debug(f"Configs will be sourced from {source_from}")
    return source_from


_T = typing.TypeVar("_T")


@dataclasses.dataclass
class _ConfigClassMeta:
    """Container for config class metadata."""

    prefix: str
    source_from: _SOURCE_FROM_OPTIONS


def config(*, prefix: str) -> typing.Callable[[_T], _T]:
    def _wrap(cls: _T) -> _T:
        return _process_config_class(cls=cls, prefix=prefix)

    return _wrap


def _process_config_class(cls: _T, prefix: str) -> _T:
    try:
        cls._meta = _ConfigClassMeta(prefix=prefix, source_from=_get_config_source())

        _enforce_upper_case_prefix(cls=cls)
        _enforce_upper_case_config_options(cls=cls)
        _enforce_config_options_types(cls=cls)
        _load_config(cls=cls)
    except Exception as e:
        _log.exception(e)
        raise

    return cls


def _enforce_upper_case_prefix(cls: _T) -> None:
    if cls._meta.prefix.upper() != cls._meta.prefix:
        raise ValueError("Prefix must be uppercase to ensure consistency")


def _enforce_upper_case_config_options(cls: _T) -> None:
    for key in cls.__annotations__.keys():
        if key.upper() != key:
            raise ValueError("All config options must be uppercase to ensure consistency")


def _enforce_config_options_types(cls: _T) -> None:
    for config_option, data_type in cls.__annotations__.items():
        try:
            type_is_supported = _config_decoder.type_is_supported(data_type=data_type)
        except Exception:
            type_is_supported = False
        if not type_is_supported:
            raise TypeError(f"Config option {config_option} type {data_type} not supported")


def _load_config(cls: _T) -> _T:
    unprocessed_config = _get_config(cls=cls)
    processed_config = _process_config(cls=cls, unprocessed_config=unprocessed_config)
    _apply_config_to_config_class(cls=cls, config=processed_config)
    return cls


def _get_config(cls: _T) -> typing.Dict[str, str]:
    if isinstance(cls._meta.source_from, _EnvironmentVariables):
        return _get_config_from_environment_variables(prefix=cls._meta.prefix)
    elif isinstance(cls._meta.source_from, _LocalFile):
        return _get_config_from_local_file(prefix=cls._meta.prefix, filepath=cls._meta.source_from.filepath)
    else:
        # this should never happen
        raise AssertionError(f"Loading config from: {cls._meta.source_from} is not supported.")


def _get_config_from_environment_variables(prefix: str) -> typing.Dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.startswith(prefix)}


def _get_config_from_local_file(prefix: str, filepath: str) -> typing.Dict[str, str]:
    try:
        config_document = pathlib.Path(filepath).read_text()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {filepath}") from e
    except PermissionError as e:
        raise PermissionError(f"Encountered a permission error when trying to read file: {filepath}") from e

    return _parse_config_document(prefix=prefix, config_document=config_document)


def _parse_config_document(prefix: str, config_document: str) -> typing.Dict[str, str]:
    config = {}
    unparsed_config_lines = config_document.strip().split(_CONFIG_DOCUMENT_FILE_LINE_SEPARATOR)
    for line in unparsed_config_lines:
        key, value = line.split(_CONFIG_DOCUMENT_KEY_VALUE_SEPARATOR, 1)
        if key.startswith(prefix):
            config[key] = value
    return config


def _process_config(cls: _T, unprocessed_config: typing.Dict[str, str]) -> typing.Dict[str, typing.Any]:
    processed_config = {}
    for key, unprocessed_value in unprocessed_config.items():
        config_option = key.split(cls._meta.prefix, 1)[1]
        if not config_option:
            _log.warning(f"Found empty config option key: {key}")
            continue
        if config_option not in cls.__annotations__:
            _log.warning(f"Config option not supported: {key}")
            continue

        processed_value = _process_config_value(
            cls=cls, config_option=config_option, unprocessed_value=unprocessed_value
        )
        processed_config[config_option] = processed_value

    return processed_config


def _process_config_value(cls: _T, config_option: str, unprocessed_value: str) -> typing.Any:
    config_option_data_type = cls.__annotations__[config_option]
    try:
        processed_value = _config_decoder.decode_config_value(
            maybe_string=unprocessed_value, data_type=config_option_data_type
        )
    except ValueError as e:
        raise ValueError(
            f"Could not cast config option {cls._meta.prefix}{config_option} with value {unprocessed_value} to datatype "
            f"{config_option_data_type}",
        ) from e

    return processed_value


def _apply_config_to_config_class(cls: _T, config: typing.Dict[str, str]) -> None:
    unset = object()
    for config_option, data_type in cls.__annotations__.items():
        default = getattr(cls, config_option, unset)
        config_option_is_optional = _optional._is_optional_type(data_type=data_type)
        config_value = config.get(config_option, unset)

        if config_value is not unset:
            setattr(cls, config_option, config_value)
        elif default is not unset:
            setattr(cls, config_option, default)  # redundant, but more readable
        elif config_option_is_optional:
            setattr(cls, config_option, None)
        else:
            raise ValueError(f"Required config option {cls._meta.prefix}{config_option} with no default was not set")

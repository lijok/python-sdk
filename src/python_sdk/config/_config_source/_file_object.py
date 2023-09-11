import os
import pathlib
import typing

from python_sdk import config
from python_sdk.config._config_source import _static_dictionary


class FileObject:
    TYPE: str = "FILE_OBJECT"

    NAME: str = "File Object"
    DESCRIPTION: str = """
    Sources configuration from a given file object.
    The file object is interpreted as a plain text document.
    The document must use `=` as a key value separator and `\n` as a new line separator.

    Example valid document:
    ```
    DB_USER=admin
    DB_PORT=5432
    ```
    """

    key_value_separator: str = "="
    line_separator: str = "\n"
    file: typing.TextIO

    def __init__(self, file: typing.TextIO | None = None) -> None:
        self.file = file or Config.FILEPATH.open(mode="r", encoding="utf-8")

    def __call__(self, prefix: str) -> dict[str, str]:
        """
        Raises:
            ValueError: Could not parse the config file, which may be malformed.
        """
        configuration = {}

        for line in self.file.read().split(self.line_separator):
            if self.key_value_separator not in line:
                raise ValueError(f"No key value separator `{self.key_value_separator}` in config line: {line}")
            key, val = line.split(self.key_value_separator, 1)
            configuration[key] = val

        return _static_dictionary.StaticDictionary(dictionary=dict(os.environ))(prefix=prefix)


class Config(
    config.Config,
    option_prefix="PYTHON_SDK_CONFIG_SOURCE_FILE_OBJECT_",
    lazy_load=True,
):
    FILEPATH: pathlib.Path = config.Option(validators=[config.ValidateFileExists(), config.ValidatePathIsReadable()])

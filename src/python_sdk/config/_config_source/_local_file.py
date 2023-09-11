import pathlib

from python_sdk import config
from python_sdk.config._config_source import _file_object


class LocalFile:
    TYPE: str = "LOCAL_FILE"

    NAME: str = "Local File"
    DESCRIPTION: str = """
    Sources configuration from a given local file.
    The file is interpreted as a plain text document.
    The document must use `=` as a key value separator and `\n` as a new line separator.

    Example valid document:
    ```
    DB_USER=admin
    DB_PORT=5432
    ```
    """

    key_value_separator: str = "="
    line_separator: str = "\n"
    filepath: pathlib.Path

    def __init__(self, filepath: pathlib.Path | None = None) -> None:
        self.filepath = filepath or Config.FILEPATH

    def __call__(self, prefix: str) -> dict[str, str]:
        """
        Raises:
            PermissionError: Could not read from config source.
            ValueError: Could not parse the config file, which may be malformed.
        """
        with self.filepath.open(mode="r", encoding="utf-8") as f:
            return _file_object.FileObject(file=f)(prefix=prefix)


class Config(
    config.Config,
    option_prefix="PYTHON_SDK_CONFIG_SOURCE_LOCAL_FILE_",
    lazy_load=True,
):
    FILEPATH: pathlib.Path = config.Option(validators=[config.ValidateFileExists(), config.ValidatePathIsReadable()])

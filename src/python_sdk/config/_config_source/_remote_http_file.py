import urllib.error
import urllib.request

import python_sdk
from python_sdk import config
from python_sdk.config._config_source import _file_object


class RemoteHTTPFile:
    TYPE: str = "REMOTE_HTTP_FILE"

    NAME: str = "Remote HTTP File"
    DESCRIPTION: str = """
    Sources configuration from a remote HTTP server at a given URL.
    The contents are interpreted as a plain text document.
    The document must use `=` as a key value separator and `\n` as a new line separator.

    Example valid document:
    ```
    DB_USER=admin
    DB_PORT=5432
    ```
    """
    url: str
    timeout: int
    authorization_header: str | None
    user_agent_string: str

    def __init__(
        self,
        url: str | None = None,
        timeout: int | None = None,
        authorization_header: str | None = None,
        user_agent_string: str | None = None,
    ) -> None:
        self.url = url or self.Config.URL
        self.timeout = timeout or self.Config.TIMEOUT
        self.authorization_header = authorization_header or self.Config.AUTHORIZATION_HEADER
        self.user_agent_string = user_agent_string or self.Config.USER_AGENT_STRING

        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            raise ValueError("RemoteHTTPFile only supports http and https endpoints.")

    def __call__(self, prefix: str) -> dict[str, str]:
        """
        Raises:
            PermissionError: Could not read from config source.
            ConnectionError: Could not connect to a networked config source.
            ValueError: Could not parse the config file, which may be malformed.
        """
        try:
            request = urllib.request.urlopen(url=self.url, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            if 400 <= e.code <= 500:
                raise PermissionError(f"Received status code {e.code} {e.reason} when connecting to {self.url}.") from e
            raise ConnectionError(f"Received status code {e.code} {e.reason} when connecting to {self.url}.") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"Could not connect to {self.url}. Malformed URL?") from e

        return _file_object.FileObject(file=request)(prefix=prefix)


class Config(
    config.Config,
    option_prefix="PYTHON_SDK_CONFIG_SOURCE_REMOTE_HTTP_FILE_",
    lazy_load=True,
):
    URL: str | None = config.Option()
    TIMEOUT: int = config.Option(default=10)
    AUTHORIZATION_HEADER: str | None = config.Option()
    USER_AGENT_STRING: str = config.Option(default=f"python-sdk-{python_sdk.__version__}")

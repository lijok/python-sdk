class S3File:
    TYPE: str = "S3_FILE"
    NAME: str = "S3 File"
    DESCRIPTION: str = """
    Sources configuration from an S3 (Simple Storage Service) compatible API.
    The file is interpreted as a plain text document.
    The document must use `=` as a key value separator and `\n` as a new line separator.

    Example valid document:
    ```
    DB_USER=admin
    DB_PORT=5432
    ```
    """

    def __call__(self, prefix: str) -> dict[str, str]:
        """
        Raises:
            PermissionError: Could not read from config source.
            ConnectionError: Could not connect to a networked config source.
            ValueError: Could not parse the config file, which may be malformed.
        """
        return {}

class AWSParameterStoreDocument:
    TYPE: str = "AWS_PARAMETER_STORE_DOCUMENT"
    NAME: str = "AWS Parameter Store document"
    DESCRIPTION: str = """
    Sources configuration from an AWS Parameter Store document.
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

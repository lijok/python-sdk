class AWSSecretsManagerSecret:
    TYPE: str = "AWS_SECRETS_MANAGER_SECRET"
    NAME: str = "AWS Secrets Manager secret"
    DESCRIPTION: str = """
    Sources configuration from an AWS Secrets Manager secret.
    The secret is interpreted as a plain text document.
    The secret must use `=` as a key value separator and `\n` as a new line separator.

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

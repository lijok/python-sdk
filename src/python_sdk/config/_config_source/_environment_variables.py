import os

from python_sdk.config._config_source import _static_dictionary


class EnvironmentVariables:
    TYPE: str = "ENVIRONMENT_VARIABLES"
    NAME: str = "Environment Variables"
    DESCRIPTION: str = "Sources configuration from the environment variables."

    def __call__(self, prefix: str) -> dict[str, str]:
        return _static_dictionary.StaticDictionary(dictionary=dict(os.environ))(prefix=prefix)

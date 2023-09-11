from python_sdk import config


class StaticDictionary:
    TYPE: str = "STATIC_DICTIONARY"
    NAME: str = "Static Dictionary"
    DESCRIPTION: str = "Sources configuration from a static dictionary."

    dictionary: dict[str, str]

    def __init__(self, dictionary: dict[str, str] | None = None) -> None:
        self.dictionary = dictionary or Config.DICTIONARY

    def __call__(self, prefix: str) -> dict[str, str]:
        return {key: val for key, val in self.dictionary.items() if key.lower().startswith(prefix.lower())}


class Config(
    config.Config,
    option_prefix="PYTHON_SDK_CONFIG_SOURCE_STATIC_DICTIONARY_",
    lazy_load=True,
):
    DICTIONARY: dict[str, str] = config.Option()

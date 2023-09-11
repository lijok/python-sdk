import typing


class ConfigSource(typing.Protocol):
    """
    Config source protocol.
    Implementing classes must only concern themselves with reading in the configuration and presenting it as a plain,
    flat, dictionary.
    Implementing classes should not attempt any config value manipulation or even normalization
    (e.g. stripping blank characters), unless said manipulation is to remove artifacts specific to the configuration
    source.
    Implementing classes should be casing-agnostic.
    Implementing classes should facilitate configuration in both, code, and runtime, by sourcing any configuration
    they require from a config class (see StaticDictionary for an example) as a fallback.
    """

    TYPE: str
    NAME: str
    DESCRIPTION: str

    def __call__(self, prefix: str) -> dict[str, str]:
        """
        Raises:
            PermissionError: Could not read from config source.
            ConnectionError: Could not connect to a networked config source.
            ValueError: Could not parse the config file, which may be malformed.
        """
        ...

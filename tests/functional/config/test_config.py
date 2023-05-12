import os
import pathlib
import typing

import pytest

from python_sdk import config


@pytest.fixture(scope="function", autouse=True)
def remove_test_env_vars() -> typing.Generator[None, None, None]:
    yield
    for key in os.environ:
        if key.startswith("TEST_"):
            print("popping", key)
            os.environ.pop(key)


def test_set_mandatory_option_is_present_in_config() -> None:
    os.environ["TEST_KEY"] = "/tmp"

    class Config(config.Config):
        TEST_KEY: pathlib.Path = config.Option()

    assert Config.TEST_KEY == pathlib.Path("/tmp")


def test_unset_mandatory_option_defaults_to_provided_default() -> None:
    class Config(config.Config):
        TEST_KEY: pathlib.Path = config.Option(default=pathlib.Path("/var"))

    assert Config.TEST_KEY == pathlib.Path("/var")


def test_unset_optional_option_is_none() -> None:
    class Config(config.Config):
        TEST_KEY: pathlib.Path | None = config.Option()

    assert Config.TEST_KEY is None


def test_unset_optional_option_defaults_to_provided_default() -> None:
    class Config(config.Config):
        TEST_KEY: pathlib.Path | None = config.Option(default=pathlib.Path("/var"))

    assert Config.TEST_KEY == pathlib.Path("/var")


# fmt: off
@pytest.mark.parametrize(
        ["data_type",                               "value",             "expected_value"],
    [
        (str,                                       "test",              "test"),
        (int,                                       "1",                 1),
        (float,                                     "1.5",               1.5),
        (bool,                                      "TRUE",              True),
        (dict[str, typing.Any],                    "{}",                {}),
        (config.Base64EncodedString,                "dGVzdA==",          config.Base64EncodedString("dGVzdA==")),
        (pathlib.Path,                              "/tmp",              pathlib.Path("/tmp")),
        (list[str],                                 "one,two",           ["one", "two"]),
        (list[int],                                 "1,2",               [1, 2]),
        (list[float],                               "1.5,1.5",           [1.5, 1.5]),
        (list[config.Base64EncodedString],          "dGVzdA==,dGVzdA==", ["dGVzdA==", "dGVzdA=="]),
        (list[pathlib.Path],                        "/tmp,/home",        [pathlib.Path("/tmp"), pathlib.Path("/home")]),
        (str | None,                                "test",              "test"),
        (int | None,                                "1",                 1),
        (float | None,                              "1.5",               1.5),
        (bool | None,                               "TRUE",              True),
        (dict[str, typing.Any] | None,             "{}",                {}),
        (config.Base64EncodedString | None,         "dGVzdA==",          config.Base64EncodedString("dGVzdA==")),
        (pathlib.Path | None,                       "/tmp",              pathlib.Path("/tmp")),
        (list[str] | None,                          "one,two",           ["one", "two"]),
        (list[int] | None,                          "1,2",               [1, 2]),
        (list[float] | None,                        "1.5,1.5",           [1.5, 1.5]),
        (list[config.Base64EncodedString] | None,   "dGVzdA==,dGVzdA==", ["dGVzdA==", "dGVzdA=="]),
        (list[pathlib.Path] | None,                 "/tmp,/home",        [pathlib.Path("/tmp"), pathlib.Path("/home")]),
        (typing.Literal["ONE"],                     "ONE",               "ONE"),
        (typing.Literal["ONE"] | None,              "ONE",               "ONE"),  # type: ignore
        (list[typing.Literal["ONE", "TWO"]] | None, "ONE,TWO",           ["ONE", "TWO"]),
    ],
)
# fmt: on
def test_config_value_when_set_is_retrieved_and_converted_correctly(
    data_type: config.ConfigValueType, value: str, expected_value: config.ConfigValueType
) -> None:
    os.environ["TEST_KEY"] = value
    cls = type(
        "Config",
        (config.Config,),
        {"__annotations__": {"TEST_KEY": data_type}, "TEST_KEY": config.Option()},
    )
    assert getattr(cls, "TEST_KEY") == expected_value


def test_options_support_lambda_defaults() -> None:
    class Config(config.Config):
        TEST_KEY: pathlib.Path = config.Option(default=lambda: pathlib.Path("/var"))

    assert Config.TEST_KEY == pathlib.Path("/var")


def test_options_support_callable_defaults() -> None:
    class Config(config.Config):
        TEST_KEY: dict[str, typing.Any] = config.Option(default=dict)

    assert Config.TEST_KEY == {}


def test_options_support_secrets(random_aws_ps_secret_string: tuple[str, str]) -> None:
    secret_key, secret_value = random_aws_ps_secret_string
    os.environ["TEST_KEY"] = f"secret:{secret_key}"

    class Config(config.Config):
        TEST_KEY: str = config.Option()

    assert Config.TEST_KEY == secret_value

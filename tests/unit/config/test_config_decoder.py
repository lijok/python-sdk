import typing

import pytest

from python_sdk.config import _config_decoder


# TODO(lijok): replace as many of these as we can with property tests
@pytest.mark.parametrize(
    "maybe_string,data_type,expected_result",
    [
        # str_to_str
        ("test", str, "test"),
        ("test,", str, "test,"),
        (",", str, ","),
        (", ", str, ", "),
        (" , ", str, " , "),
        (" ", str, " "),
        ("", str, ValueError),
        (None, str, ValueError),
        # str_to_int
        ("5", int, 5),
        ("5 ", int, ValueError),
        (" 5", int, ValueError),
        ("5.5", int, ValueError),
        ("test", int, ValueError),
        ("", int, ValueError),
        (None, int, ValueError),
        # str_to_float
        ("5.5", float, 5.5),
        ("5", float, 5.0),
        ("5 ", float, ValueError),
        (" 5", float, ValueError),
        ("test", float, ValueError),
        ("", float, ValueError),
        (None, float, ValueError),
        # str_to_bool
        ("true", bool, True),
        ("True", bool, True),
        ("TRUE", bool, True),
        ("false", bool, False),
        ("False", bool, False),
        ("FALSE", bool, False),
        ("FALSE ", bool, ValueError),
        (" FALSE", bool, ValueError),
        ("a", bool, ValueError),
        ("yes", bool, ValueError),
        ("no", bool, ValueError),
        ("", bool, ValueError),
        ("1", bool, ValueError),
        ("0", bool, ValueError),
        (None, bool, ValueError),
        # str_to_unvalidated_dict
        ('{"test": "test"}', _config_decoder.UnvalidatedDict, {"test": "test"}),
        ('{"test": "test"}   ', _config_decoder.UnvalidatedDict, ValueError),
        (' {"test": "test"}', _config_decoder.UnvalidatedDict, ValueError),
        ('{"test": "test"', _config_decoder.UnvalidatedDict, ValueError),
        ("{'test': 'test'}", _config_decoder.UnvalidatedDict, ValueError),
        ("test", _config_decoder.UnvalidatedDict, ValueError),
        ("1", _config_decoder.UnvalidatedDict, ValueError),
        ("[]", _config_decoder.UnvalidatedDict, ValueError),
        ("", _config_decoder.UnvalidatedDict, ValueError),
        # str_to_base64_encoded_string
        ("dGVzdA==", _config_decoder.Base64EncodedString, "dGVzdA=="),
        ("dGVzdA== ", _config_decoder.Base64EncodedString, ValueError),
        (" dGVzdA==", _config_decoder.Base64EncodedString, ValueError),
        ("??!@", _config_decoder.Base64EncodedString, ValueError),
        ("test", _config_decoder.Base64EncodedString, ValueError),
        ("", _config_decoder.Base64EncodedString, ValueError),
        (None, _config_decoder.Base64EncodedString, ValueError),
        # str_to_literal
        ("INFO", typing.Literal["INFO"], "INFO"),
        ("DEBUG", typing.Literal["INFO", "DEBUG"], "DEBUG"),
        ("info", typing.Literal["INFO"], ValueError),
        ("", typing.Literal["INFO"], ValueError),
        (None, typing.Literal["INFO"], ValueError),
        # str_to_list_of_strs
        ("one,two,three", typing.List[str], ["one", "two", "three"]),
        ("one", typing.List[str], ["one"]),
        ('["one"]', typing.List[str], ['["one"]']),
        ("[]", typing.List[str], ["[]"]),
        ("one,two,three,", typing.List[str], ValueError),
        ("one,", typing.List[str], ValueError),
        (",one", typing.List[str], ValueError),
        (" one", typing.List[str], ValueError),
        ("one, ", typing.List[str], ValueError),
        ("", typing.List[str], ValueError),
        (",", typing.List[str], ValueError),
        (" ,", typing.List[str], ValueError),
        (", ", typing.List[str], ValueError),
        (" , ", typing.List[str], ValueError),
        # str_to_list_of_ints
        ("1,2,3", typing.List[int], [1, 2, 3]),
        ("1", typing.List[int], [1]),
        ("1,2,3,", typing.List[int], ValueError),
        ("1,", typing.List[int], ValueError),
        (",1", typing.List[int], ValueError),
        (" 1", typing.List[int], ValueError),
        ("1, ", typing.List[int], ValueError),
        ("1.2,1.5", typing.List[int], ValueError),
        ('["1"]', typing.List[int], ValueError),
        ("[]", typing.List[int], ValueError),
        ("[1]", typing.List[int], ValueError),
        ("", typing.List[int], ValueError),
        (",", typing.List[int], ValueError),
        (" ,", typing.List[int], ValueError),
        (", ", typing.List[int], ValueError),
        (" , ", typing.List[int], ValueError),
        # str_to_list_of_floats
        ("1.5,2.5,3.5", typing.List[float], [1.5, 2.5, 3.5]),
        ("1.5", typing.List[float], [1.5]),
        ("1.5,2.5,3.5,", typing.List[float], ValueError),
        ("1,2,3,", typing.List[float], ValueError),
        ("1.5,", typing.List[float], ValueError),
        (",1.5", typing.List[float], ValueError),
        (" 1.5", typing.List[float], ValueError),
        ("1.5, ", typing.List[float], ValueError),
        ('["1.5"]', typing.List[float], ValueError),
        ("[]", typing.List[float], ValueError),
        ("[1.5]", typing.List[float], ValueError),
        ("", typing.List[float], ValueError),
        (",", typing.List[float], ValueError),
        (" ,", typing.List[float], ValueError),
        (", ", typing.List[float], ValueError),
        (" , ", typing.List[float], ValueError),
        # str_to_list_of_base64_encoded_strings
        (
            "dGVzdA==,dGVzdA==,dGVzdA==",
            typing.List[_config_decoder.Base64EncodedString],
            ["dGVzdA==", "dGVzdA==", "dGVzdA=="],
        ),
        ("dGVzdA==", typing.List[_config_decoder.Base64EncodedString], ["dGVzdA=="]),
        (
            "dGVzdA==,dGVzdA==,dGVzdA==,",
            typing.List[_config_decoder.Base64EncodedString],
            ValueError,
        ),
        ("dGVzdA==,", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (" dGVzdA==", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (",dGVzdA==", typing.List[_config_decoder.Base64EncodedString], ValueError),
        ("dGVzdA==,  ", typing.List[_config_decoder.Base64EncodedString], ValueError),
        ('["dGVzdA=="]', typing.List[_config_decoder.Base64EncodedString], ValueError),
        ("[]", typing.List[_config_decoder.Base64EncodedString], ValueError),
        ("", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (",", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (" ,", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (", ", typing.List[_config_decoder.Base64EncodedString], ValueError),
        (" , ", typing.List[_config_decoder.Base64EncodedString], ValueError),
        # str_to_list_of_literals
        ("INFO", typing.List[typing.Literal["INFO"]], ["INFO"]),
        ("DEBUG", typing.List[typing.Literal["INFO", "DEBUG"]], ["DEBUG"]),
        ("INFO,DEBUG", typing.List[typing.Literal["INFO", "DEBUG"]], ["INFO", "DEBUG"]),
        ("info", typing.List[typing.Literal["INFO"]], ValueError),
        ("INFO,", typing.List[typing.Literal["INFO"]], ValueError),
        ("INFO ", typing.List[typing.Literal["INFO"]], ValueError),
        (",INFO ", typing.List[typing.Literal["INFO"]], ValueError),
        (" INFO ", typing.List[typing.Literal["INFO"]], ValueError),
        ("", typing.List[typing.Literal["INFO"]], ValueError),
        (None, typing.List[typing.Literal["INFO"]], ValueError),
        # str_to_optional_str
        ("test", typing.Optional[str], "test"),
        ("test,", typing.Optional[str], "test,"),
        (" ", typing.Optional[str], " "),
        (" ,", typing.Optional[str], " ,"),
        ("", typing.Optional[str], None),
        (None, typing.Optional[str], None),
        # str_to_optional_int
        ("1", typing.Optional[int], 1),
        ("", typing.Optional[int], None),
        (None, typing.Optional[int], None),
        ("1 ", typing.Optional[int], ValueError),
        (" 1", typing.Optional[int], ValueError),
        ("test", typing.Optional[int], ValueError),
        ("1,", typing.Optional[int], ValueError),
        ("1.5", typing.Optional[int], ValueError),
        (" ", typing.Optional[int], ValueError),
        # str_to_optional_float
        ("1.5", typing.Optional[float], 1.5),
        ("1", typing.Optional[float], 1.0),
        ("", typing.Optional[float], None),
        (None, typing.Optional[float], None),
        ("1.5 ", typing.Optional[float], ValueError),
        (" 1.5", typing.Optional[float], ValueError),
        ("test", typing.Optional[float], ValueError),
        (" ", typing.Optional[float], ValueError),
        # str_to_optional_bool
        ("true", typing.Optional[bool], True),
        ("false", typing.Optional[bool], False),
        ("", typing.Optional[bool], None),
        (None, typing.Optional[bool], None),
        ("yes", typing.Optional[bool], ValueError),
        ("true ", typing.Optional[bool], ValueError),
        (" true", typing.Optional[bool], ValueError),
        ("false ", typing.Optional[bool], ValueError),
        # str_to_optional_unvalidated_dict
        ('{"test": "test"}', typing.Optional[_config_decoder.UnvalidatedDict], {"test": "test"}),
        ("", typing.Optional[_config_decoder.UnvalidatedDict], None),
        (None, typing.Optional[_config_decoder.UnvalidatedDict], None),
        (' {"test": "test"}', typing.Optional[_config_decoder.UnvalidatedDict], ValueError),
        ('{"test": "test"} ', typing.Optional[_config_decoder.UnvalidatedDict], ValueError),
        # str_to_optional_base64_encoded_string
        ("dGVzdA==", typing.Optional[_config_decoder.Base64EncodedString], "dGVzdA=="),
        ("", typing.Optional[_config_decoder.Base64EncodedString], None),
        (None, typing.Optional[_config_decoder.Base64EncodedString], None),
        (" dGVzdA==", typing.Optional[_config_decoder.Base64EncodedString], ValueError),
        ("dGVzdA== ", typing.Optional[_config_decoder.Base64EncodedString], ValueError),
        # str_to_optional_literal
        ("INFO", typing.Optional[typing.Literal["INFO"]], "INFO"),
        ("DEBUG", typing.Optional[typing.Literal["INFO", "DEBUG"]], "DEBUG"),
        ("", typing.Optional[typing.Literal["INFO"]], None),
        (None, typing.Optional[typing.Literal["INFO"]], None),
        ("info", typing.Optional[typing.Literal["INFO"]], ValueError),
        # str_to_optional_list_of_strs
        ("one,two,three", typing.Optional[typing.List[str]], ["one", "two", "three"]),
        ("one ,two", typing.Optional[typing.List[str]], ["one ", "two"]),
        ("", typing.Optional[typing.List[str]], None),
        (None, typing.Optional[typing.List[str]], None),
        ("one ", typing.Optional[typing.List[str]], ValueError),
        ("one,", typing.Optional[typing.List[str]], ValueError),
        (" one", typing.Optional[typing.List[str]], ValueError),
        (",one", typing.Optional[typing.List[str]], ValueError),
        # str_to_optional_list_of_ints
        ("1,2,3", typing.Optional[typing.List[int]], [1, 2, 3]),
        ("", typing.Optional[typing.List[int]], None),
        (None, typing.Optional[typing.List[int]], None),
        ("1 ", typing.Optional[typing.List[int]], ValueError),
        ("1 ,", typing.Optional[typing.List[int]], ValueError),
        ("1,", typing.Optional[typing.List[int]], ValueError),
        (",1", typing.Optional[typing.List[int]], ValueError),
        (" 1", typing.Optional[typing.List[int]], ValueError),
        # str_to_optional_list_of_floats
        ("1.5,2.5,3.5", typing.Optional[typing.List[float]], [1.5, 2.5, 3.5]),
        ("", typing.Optional[typing.List[float]], None),
        (None, typing.Optional[typing.List[float]], None),
        ("1.5 ", typing.Optional[typing.List[float]], ValueError),
        ("1.5 ,", typing.Optional[typing.List[float]], ValueError),
        ("1.5,", typing.Optional[typing.List[float]], ValueError),
        (",1.5", typing.Optional[typing.List[float]], ValueError),
        (" 1.5", typing.Optional[typing.List[float]], ValueError),
        # str_to_optional_list_of_base64_encoded_strings
        (
            "dGVzdA==,dGVzdA==,dGVzdA==",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ["dGVzdA==", "dGVzdA==", "dGVzdA=="],
        ),
        ("", typing.Optional[typing.List[_config_decoder.Base64EncodedString]], None),
        (None, typing.Optional[typing.List[_config_decoder.Base64EncodedString]], None),
        (
            "dGVzdA== ,dGVzdA==",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ValueError,
        ),
        (
            "dGVzdA==,",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ValueError,
        ),
        (
            "dGVzdA== ",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ValueError,
        ),
        (
            ",dGVzdA==",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ValueError,
        ),
        (
            " dGVzdA==",
            typing.Optional[typing.List[_config_decoder.Base64EncodedString]],
            ValueError,
        ),
        # str_to_optional_list_of_literals
        ("INFO", typing.Optional[typing.List[typing.Literal["INFO"]]], ["INFO"]),
        ("DEBUG", typing.Optional[typing.List[typing.Literal["INFO", "DEBUG"]]], ["DEBUG"]),
        (
            "INFO,DEBUG",
            typing.Optional[typing.List[typing.Literal["INFO", "DEBUG"]]],
            ["INFO", "DEBUG"],
        ),
        ("", typing.Optional[typing.List[typing.Literal["INFO"]]], None),
        (None, typing.Optional[typing.List[typing.Literal["INFO"]]], None),
        ("info", typing.Optional[typing.List[typing.Literal["INFO"]]], ValueError),
        ("INFO,", typing.Optional[typing.List[typing.Literal["INFO"]]], ValueError),
        ("INFO ", typing.Optional[typing.List[typing.Literal["INFO"]]], ValueError),
        (",INFO ", typing.Optional[typing.List[typing.Literal["INFO"]]], ValueError),
        (" INFO ", typing.Optional[typing.List[typing.Literal["INFO"]]], ValueError),
    ],
)
def test_decode_config_value(
    maybe_string: typing.Optional[str],
    data_type: typing.Type,
    expected_result: typing.Any,
) -> None:
    if expected_result == ValueError:
        with pytest.raises(expected_result):
            _config_decoder.decode_config_value(maybe_string=maybe_string, data_type=data_type)
    else:
        result = _config_decoder.decode_config_value(maybe_string=maybe_string, data_type=data_type)
        assert result == expected_result

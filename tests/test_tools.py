import pytest

from dennis.tools import (
    VariableTokenizer,
    PythonFormat,
    PythonBraceFormat,
    parse_dennis_note,
)


def test_empty_tokenizer():
    vartok = VariableTokenizer([])
    assert vartok.contains("python-format") is False
    assert vartok.tokenize("a b c d e") == ["a b c d e"]
    assert vartok.extract_tokens("a b c d e") == set()
    assert vartok.is_token("{0}") is False
    assert vartok.extract_variable_name("{0}") is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello %s", ["Hello ", "%s"]),
        ("Hello %(username)s", ["Hello ", "%(username)s"]),
        ("Hello %(user)s%(name)s", ["Hello ", "%(user)s", "%(name)s"]),
        ("Hello {username}", ["Hello ", "{username}"]),
        ("Hello {user}{name}", ["Hello ", "{user}", "{name}"]),
        ("Products and Services", ["Products and Services"]),
    ],
)
def test_python_tokenizing(text, expected):
    vartok = VariableTokenizer(["python-format", "python-brace-format"])
    assert vartok.tokenize(text) == expected


class TestPythonBraceFormat:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", ["Hello"]),
            ("{foo}", ["{foo}"]),
            ("Hello {foo}", ["Hello ", "{foo}"]),
            ("{foo} Hello", ["{foo}", " Hello"]),
            ("{foo:%Y-%m-%d}", ["{foo:%Y-%m-%d}"]),
            ("{foo:%Y-%m-%d %H:%M}", ["{foo:%Y-%m-%d %H:%M}"]),
        ],
    )
    def test_parse(self, text, expected):
        vartok = VariableTokenizer(["python-brace-format"])
        assert vartok.tokenize(text) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("{}", ""),
            ("{0}", "0"),
            ("{abc}", "abc"),
            ("{abc.def}", "abc.def"),
            ("{abc[0]}", "abc[0]"),
            ("{abc!s}", "abc"),  # conversion
            ("{abc: >16}", "abc"),  # format_spec
        ],
    )
    def test_variable_name(self, text, expected):
        v = PythonBraceFormat()
        assert v.extract_variable_name(text) == expected


@pytest.mark.parametrize(
    "text,expected", [("%s", ""), ("%d", ""), ("%.2f", ""), ("%(foo)s", "foo")]
)
def test_pythonformat(text, expected):
    v = PythonFormat()
    assert v.extract_variable_name(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", []),
        ("Foo", []),
        ("Foo bar", []),
        ("dennis-ignore", []),
        ("dennis-ignore: *", "*"),
        ("dennis-ignore: E101", ["E101"]),
        ("dennis-ignore: E101, E102", ["E101"]),
        ("dennis-ignore: E101,E102", ["E101", "E102"]),
        ("localizers ignore this: dennis-ignore: E101,E102", ["E101", "E102"]),
    ],
)
def test_parse_dennis_note(text, expected):
    assert parse_dennis_note(text) == expected

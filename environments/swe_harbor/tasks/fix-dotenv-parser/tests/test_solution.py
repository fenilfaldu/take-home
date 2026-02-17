import sys
sys.path.insert(0, "/app")

import pytest
from parser import parse
from variables import parse_variables
from main import parse_dotenv


# ---- Basic parsing (these pass even with the bugs) ----

def test_simple_key_value():
    assert parse("FOO=bar") == [("FOO", "bar")]


def test_multiple_pairs():
    result = parse("A=1\nB=2\nC=3")
    assert result == [("A", "1"), ("B", "2"), ("C", "3")]


def test_skip_comments():
    result = parse("# comment\nFOO=bar\n# another")
    assert result == [("FOO", "bar")]


def test_skip_blank_lines():
    result = parse("\nFOO=bar\n\nBAZ=qux\n")
    assert result == [("FOO", "bar"), ("BAZ", "qux")]


def test_export_prefix():
    assert parse("export FOO=bar") == [("FOO", "bar")]


def test_single_quoted_value():
    assert parse("FOO='hello world'") == [("FOO", "hello world")]


def test_unquoted_inline_comment():
    assert parse("FOO=bar # comment") == [("FOO", "bar")]


def test_empty_value():
    assert parse("FOO=") == [("FOO", "")]


# ---- Double-quoted escape sequences (catches Bug 1) ----

def test_double_quote_newline_escape():
    result = parse(r'FOO="hello\nworld"')
    assert result == [("FOO", "hello\nworld")], (
        "Double-quoted \\n should produce an actual newline character"
    )


def test_double_quote_tab_escape():
    result = parse(r'FOO="col1\tcol2"')
    assert result == [("FOO", "col1\tcol2")], (
        "Double-quoted \\t should produce an actual tab character"
    )


def test_double_quote_escaped_quote():
    result = parse(r'FOO="say \"hi\""')
    assert result == [("FOO", 'say "hi"')], (
        'Double-quoted \\" should produce a literal double-quote'
    )


def test_double_quote_escaped_backslash():
    result = parse(r'FOO="back\\slash"')
    assert result == [("FOO", "back\\slash")], (
        "Double-quoted \\\\ should produce a single backslash"
    )


def test_single_quote_no_newline_escape():
    """Single-quoted values should NOT decode \\n as a newline."""
    result = parse("FOO='hello\\nworld'")
    assert result == [("FOO", "hello\\nworld")], (
        "Single-quoted \\n should stay literal"
    )


# ---- Variable interpolation (catches Bug 2) ----

def test_simple_variable_reference():
    result = parse_dotenv("A=hello\nB=${A}")
    assert result["B"] == "hello"


def test_default_value_when_undefined():
    result = parse_dotenv("A=${UNDEFINED:-fallback}")
    assert result["A"] == "fallback", (
        "${UNDEFINED:-fallback} should resolve to 'fallback' "
        "when UNDEFINED is not set"
    )


def test_default_not_used_when_defined():
    result = parse_dotenv("A=real\nB=${A:-fallback}")
    assert result["B"] == "real", (
        "${A:-fallback} should resolve to 'real' when A is defined"
    )


def test_multiple_variable_references():
    result = parse_dotenv("HOST=localhost\nPORT=5432\nURL=${HOST}:${PORT}/db")
    assert result["URL"] == "localhost:5432/db"


def test_default_in_context():
    result = parse_dotenv("GREETING=Hello ${NAME:-World}!")
    assert result["GREETING"] == "Hello World!", (
        "${NAME:-World} should resolve to 'World' when NAME is not set"
    )


def test_undefined_no_default():
    result = parse_dotenv("A=${MISSING}")
    assert result["A"] == "", (
        "${MISSING} with no default should resolve to empty string"
    )


# ---- Integration ----

def test_full_config():
    content = (
        "# Database\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=myapp\n"
        'DB_URL="postgres://${DB_HOST}:${DB_PORT}/${DB_NAME}"\n'
        "\n"
        "# Defaults\n"
        "LOG_LEVEL=${LOG_LEVEL:-info}\n"
    )
    result = parse_dotenv(content)
    assert result["DB_HOST"] == "localhost"
    assert result["DB_URL"] == "postgres://localhost:5432/myapp"
    assert result["LOG_LEVEL"] == "info"

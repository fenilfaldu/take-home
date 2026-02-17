# Fix the dotenv parser

You are working on a small `.env` file parser written in Python. The project has three modules:

- **`parser.py`** — reads `.env` file content and extracts key-value pairs. Handles single-quoted, double-quoted, and unquoted values with escape sequence processing.
- **`variables.py`** — handles `${VAR}` and `${VAR:-default}` variable interpolation in values.
- **`main.py`** — combines parsing and variable resolution into a single `parse_dotenv()` function.

## The problem

The parser has **2 bugs** that cause incorrect behavior:

1. **Escape sequences in double-quoted values are not decoded properly.** For example, `FOO="hello\nworld"` should produce a value with an actual newline character, but the parser returns the literal characters `\n` instead.

2. **Variable interpolation ignores default values.** For example, `A=${UNDEFINED:-fallback}` should resolve to `"fallback"` when `UNDEFINED` is not set, but the parser returns an empty string instead.

## What to fix

Find and fix both bugs. The bugs are in `parser.py` and `variables.py`. The file `main.py` is correct and should not be modified.

## Expected behavior

### Escape sequences

| Input (.env line) | Expected parsed value |
|---|---|
| `FOO="hello\nworld"` | `hello` + newline + `world` |
| `FOO="col1\tcol2"` | `col1` + tab + `col2` |
| `FOO="say \"hello\""` | `say "hello"` |
| `FOO='hello\nworld'` | `hello\nworld` (literal, no decoding) |

### Variable interpolation

| Input (.env content) | Expected result |
|---|---|
| `A=${UNDEFINED:-fallback}` | `A` = `"fallback"` |
| `A=hello\nB=${A}` | `B` = `"hello"` |
| `A=${MISSING}` | `A` = `""` |

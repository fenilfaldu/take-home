#!/bin/bash

# Fix 1: parser.py — the double-quoted value branch incorrectly uses
# _single_quote_escapes instead of _double_quote_escapes, so escape
# sequences like \n, \t, \" are not decoded in double-quoted strings.
cat > /app/parser.py << 'PYEOF'
"""
dotenv parser — reads .env content and extracts key-value pairs.

Handles single-quoted, double-quoted, and unquoted values.
"""

import re

# Escape patterns recognized in each quoting style
_single_quote_escapes = re.compile(r"\\[\\']")
_double_quote_escapes = re.compile(r"\\[\\'\"abfnrtv]")

_escape_map = {
    "\\\\": "\\", "\\'": "'", '\\"': '"',
    "\\n": "\n", "\\t": "\t", "\\r": "\r",
    "\\a": "\a", "\\b": "\b", "\\f": "\f", "\\v": "\v",
}


def decode_escapes(pattern, s):
    """Replace escape sequences matched by *pattern* with their values."""
    return pattern.sub(lambda m: _escape_map.get(m.group(0), m.group(0)), s)


def _parse_value(raw):
    """Parse the value part of a KEY=VALUE line."""
    raw = raw.strip()
    if not raw:
        return ""

    if raw[0] == "'":
        m = re.match(r"^'((?:[^'\\]|\\.)*)'", raw)
        if m:
            return decode_escapes(_single_quote_escapes, m.group(1))
        return raw

    if raw[0] == '"':
        m = re.match(r'^"((?:[^"\\]|\\.)*)"', raw)
        if m:
            return decode_escapes(_double_quote_escapes, m.group(1))
        return raw

    # Unquoted: strip inline comments
    return re.sub(r"\s+#.*", "", raw).rstrip()


def parse(content):
    """Parse .env content into a list of (key, value) tuples."""
    pairs = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        pairs.append((key.strip(), _parse_value(raw)))
    return pairs
PYEOF

# Fix 2: variables.py — the default-value condition in Variable.resolve()
# is inverted: `self.default is None` should be `self.default is not None`,
# so that ${VAR:-fallback} actually uses "fallback" when VAR is undefined.
cat > /app/variables.py << 'PYEOF'
"""
Variable interpolation for dotenv values.

Supports ${VAR} and ${VAR:-default} syntax.
"""

import re

_var_re = re.compile(
    r"\$\{(?P<name>[^}:]+)(?::-(?P<default>[^}]*))?\}"
)


class Literal:
    """Plain-text segment."""
    def __init__(self, text):
        self.text = text

    def resolve(self, env):
        return self.text


class Variable:
    """A ${NAME} or ${NAME:-default} reference."""
    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def resolve(self, env):
        fallback = self.default if self.default is not None else ""
        result = env.get(self.name, fallback)
        return result if result is not None else ""


def parse_variables(value):
    """Split *value* into Literal and Variable atoms."""
    atoms = []
    last = 0
    for m in _var_re.finditer(value):
        if m.start() > last:
            atoms.append(Literal(value[last:m.start()]))
        atoms.append(Variable(m.group("name"), m.group("default")))
        last = m.end()
    if last < len(value):
        atoms.append(Literal(value[last:]))
    return atoms
PYEOF

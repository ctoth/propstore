"""CEL string escape coverage from the CEL language definition."""

from __future__ import annotations

import pytest

from propstore.cel_checker import TokenType, tokenize


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (r'"a\nb"', "a\nb"),
        (r'"\r\t"', "\r\t"),
        (r'"\a\b\f\v"', "\a\b\f\v"),
        (r'"\?\"\'\\\`"', "?\"'\\`"),
        (r'"caf\u00e9"', "caf\u00e9"),
        (r'"\x4A"', "J"),
        (r'"\X4a"', "J"),
        (r'"\000\012\177"', "\x00\n\x7f"),
        (r'"\U0001F62C"', "\U0001F62C"),
    ],
)
def test_cel_string_escape_sequences(expr: str, expected: str) -> None:
    # CEL langdef.md String Values: punctuation, whitespace, hex, Unicode,
    # and three-digit octal escapes are valid in quoted strings.
    token = tokenize(expr)[0]

    assert token.type == TokenType.STRING_LIT
    assert token.value == expected


@pytest.mark.parametrize(
    "expr",
    [
        r'"\q"',
        r'"\x4"',
        r'"\u00e"',
        r'"\U0001F62"',
        r'"\400"',
    ],
)
def test_cel_invalid_string_escapes_rejected(expr: str) -> None:
    with pytest.raises(ValueError):
        tokenize(expr)

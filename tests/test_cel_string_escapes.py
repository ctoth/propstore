"""CEL string escape coverage from the CEL language definition."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.cel_checker import TokenType, check_cel_expr, tokenize


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


_ESCAPE_CASES = (
    (r"\n", "\n"),
    (r"\r", "\r"),
    (r"\t", "\t"),
    (r"\a", "\a"),
    (r"\b", "\b"),
    (r"\f", "\f"),
    (r"\v", "\v"),
    (r"\?", "?"),
    (r"\"", '"'),
    (r"\'", "'"),
    (r"\\", "\\"),
    (r"\`", "`"),
    (r"\u00e9", "\u00e9"),
    (r"\x4A", "J"),
    (r"\000", "\x00"),
    (r"\U0001F62C", "\U0001F62C"),
)


@pytest.mark.property
@given(parts=st.lists(st.sampled_from(_ESCAPE_CASES), min_size=1, max_size=12))
@settings(deadline=None, max_examples=40)
def test_cel_string_escape_sequences_round_trip_through_parser(parts) -> None:
    """CEL langdef String Values: supported escapes decode consistently."""
    source = '"' + "".join(encoded for encoded, _ in parts) + '"'
    expected = "".join(decoded for _, decoded in parts)

    token = tokenize(source)[0]

    assert token.type == TokenType.STRING_LIT
    assert token.value == expected
    check_cel_expr(f"{source} == {source}", {})

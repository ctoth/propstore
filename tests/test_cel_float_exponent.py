"""CEL numeric literal coverage from the CEL language definition."""

from __future__ import annotations

import pytest

from cel_parser import DoubleLit, ParseError, parse


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("1e3", 1000.0),
        ("1.5e-7", 1.5e-7),
        ("2E10", 2.0e10),
        (".5e2", 50.0),
        ("7e0", 7.0),
        (".700e1", 7.0),
    ],
)
def test_cel_double_literals_accept_exponents(expr: str, expected: float) -> None:
    """CEL langdef.md Numeric Values: doubles include `7e0` and `.700e1`."""
    node = parse(expr)
    assert isinstance(node, DoubleLit)
    assert node.value == expected


@pytest.mark.parametrize("expr", ["1e", "1e+", "1e-", "1abc"])
def test_cel_malformed_number_suffix_rejected(expr: str) -> None:
    with pytest.raises(ParseError):
        parse(expr)

from __future__ import annotations

import pytest

from propstore.cel_checker import ConceptInfo, KindType, check_cel_expr


def _registry() -> dict[str, ConceptInfo]:
    return {
        "cond": ConceptInfo("cond-id", "cond", KindType.BOOLEAN),
        "x": ConceptInfo("x-id", "x", KindType.QUANTITY),
        "y": ConceptInfo("y-id", "y", KindType.QUANTITY),
    }


@pytest.mark.parametrize(
    ("expr", "message"),
    [
        ("1 ? true : false", "condition must be boolean"),
        ('cond ? 1 : "x"', "branches must have the same type"),
    ],
)
def test_cel_ternary_rejects_non_boolean_condition_and_mixed_branches(
    expr: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        check_cel_expr(expr, _registry())


@pytest.mark.parametrize("expr", ["cond ? x : y", 'cond ? "a" : "b"'])
def test_cel_ternary_accepts_boolean_condition_and_unified_branches(expr: str) -> None:
    check_cel_expr(expr, _registry())

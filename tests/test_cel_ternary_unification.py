from __future__ import annotations

import pytest

from propstore.core.conditions import check_condition_ir
from propstore.core.conditions.registry import ConceptInfo, KindType


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
        check_condition_ir(expr, _registry())


@pytest.mark.parametrize("expr", ["cond ? x : y", 'cond ? "a" : "b"'])
def test_cel_ternary_accepts_boolean_condition_and_unified_branches(expr: str) -> None:
    check_condition_ir(expr, _registry())

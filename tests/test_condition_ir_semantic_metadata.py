from __future__ import annotations

import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.core.conditions import (
    ConditionBinary,
    ConditionLiteral,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
    condition_ir_from_cel,
)


def test_timepoint_lowers_to_distinct_condition_value_kind() -> None:
    timepoint_kind = getattr(ConditionValueKind, "TIMEPOINT", None)
    assert timepoint_kind is not None

    condition = condition_ir_from_cel(
        "valid_from >= 100",
        {
            "valid_from": ConceptInfo(
                id="ps:concept:valid-from",
                canonical_name="valid_from",
                kind=KindType.TIMEPOINT,
            )
        },
    )

    assert isinstance(condition, ConditionBinary)
    assert isinstance(condition.left, ConditionReference)
    assert condition.left.value_kind == timepoint_kind


def test_category_reference_carries_open_closed_metadata() -> None:
    closed = condition_ir_from_cel(
        "task == 'speech'",
        {
            "task": ConceptInfo(
                id="ps:concept:task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "singing"],
                category_extensible=False,
            )
        },
    )

    assert isinstance(closed, ConditionBinary)
    assert isinstance(closed.left, ConditionReference)
    assert closed.left.category_values == ("speech", "singing")
    assert closed.left.category_extensible is False

    open_condition = condition_ir_from_cel(
        "task == 'dancing'",
        {
            "task": ConceptInfo(
                id="ps:concept:task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech"],
                category_extensible=True,
            )
        },
    )

    assert isinstance(open_condition, ConditionBinary)
    assert isinstance(open_condition.left, ConditionReference)
    assert open_condition.left.category_values == ("speech",)
    assert open_condition.left.category_extensible is True


def test_numeric_literal_rejects_bool_at_construction() -> None:
    with pytest.raises(TypeError, match="boolean literal cannot be numeric"):
        ConditionLiteral(
            value=True,
            value_kind=ConditionValueKind.NUMERIC,
            span=ConditionSourceSpan(0, 4),
        )


def test_bare_string_expression_fails_at_frontend_boundary() -> None:
    with pytest.raises(TypeError, match="bare string|unsupported"):
        condition_ir_from_cel("'loose'", {})

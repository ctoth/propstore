from __future__ import annotations

import importlib

import pytest

from propstore.cel_checker import ConceptInfo, KindType
from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionLiteral,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
    condition_ir_from_cel,
)
from propstore.core.id_types import ConceptId


def test_condition_ir_can_be_constructed_without_cel_or_backend_nodes() -> None:
    left = ConditionReference(
        concept_id=ConceptId("ps:concept:temperature"),
        source_name="temperature",
        value_kind=ConditionValueKind.NUMERIC,
        span=ConditionSourceSpan(start=0, end=11),
    )
    right = ConditionLiteral(
        value=21,
        value_kind=ConditionValueKind.NUMERIC,
        span=ConditionSourceSpan(start=14, end=16),
    )
    expression = ConditionBinary(
        op=ConditionBinaryOp.GREATER_THAN,
        left=left,
        right=right,
        span=ConditionSourceSpan(start=0, end=16),
    )

    assert expression.left == left
    assert expression.right == right
    assert expression.span == ConditionSourceSpan(0, 16)

    conditions = importlib.import_module("propstore.core.conditions")
    assert not hasattr(conditions, "RuntimeHelper")
    assert not hasattr(conditions, "PythonAst")
    assert not hasattr(conditions, "Z3")


def test_condition_ir_from_cel_lowers_typed_comparison() -> None:
    ir = condition_ir_from_cel(
        "temperature > 21",
        {
            "temperature": ConceptInfo(
                id="ps:concept:temperature",
                canonical_name="temperature",
                kind=KindType.QUANTITY,
            )
        },
    )

    assert ir == ConditionBinary(
        op=ConditionBinaryOp.GREATER_THAN,
        left=ConditionReference(
            concept_id=ConceptId("ps:concept:temperature"),
            source_name="temperature",
            value_kind=ConditionValueKind.NUMERIC,
            span=ConditionSourceSpan(0, 16),
        ),
        right=ConditionLiteral(
            value=21,
            value_kind=ConditionValueKind.NUMERIC,
            span=ConditionSourceSpan(0, 16),
        ),
        span=ConditionSourceSpan(0, 16),
    )


def test_condition_ir_from_cel_rejects_structural_concepts() -> None:
    with pytest.raises(ValueError, match="Structural concept"):
        condition_ir_from_cel(
            "focalization == 'internal'",
            {
                "focalization": ConceptInfo(
                    id="ps:concept:focalization",
                    canonical_name="focalization",
                    kind=KindType.STRUCTURAL,
                )
            },
        )

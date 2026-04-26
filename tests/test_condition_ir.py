from __future__ import annotations

import importlib

import pytest

from propstore.cel_checker import (
    BinaryOpNode,
    CelSourceSpan,
    ConceptInfo,
    KindType,
    LiteralNode,
    NameNode,
    parse_cel,
)
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
            span=ConditionSourceSpan(0, 11),
        ),
        right=ConditionLiteral(
            value=21,
            value_kind=ConditionValueKind.NUMERIC,
            span=ConditionSourceSpan(14, 16),
        ),
        span=ConditionSourceSpan(0, 16),
    )


def test_cel_ast_nodes_preserve_source_spans() -> None:
    ast = parse_cel("temperature > 21")

    assert isinstance(ast, BinaryOpNode)
    assert ast.span == CelSourceSpan(0, 16)
    assert isinstance(ast.left, NameNode)
    assert ast.left.span == CelSourceSpan(0, 11)
    assert isinstance(ast.right, LiteralNode)
    assert ast.right.span == CelSourceSpan(14, 16)


def test_condition_ir_preserves_child_spans_from_cel_frontend() -> None:
    ir = condition_ir_from_cel(
        "(temperature > 21) && humid",
        {
            "temperature": ConceptInfo(
                id="ps:concept:temperature",
                canonical_name="temperature",
                kind=KindType.QUANTITY,
            ),
            "humid": ConceptInfo(
                id="ps:concept:humid",
                canonical_name="humid",
                kind=KindType.BOOLEAN,
            ),
        },
    )

    assert isinstance(ir, ConditionBinary)
    assert ir.span == ConditionSourceSpan(1, 27)
    assert isinstance(ir.left, ConditionBinary)
    assert ir.left.span == ConditionSourceSpan(1, 17)
    assert isinstance(ir.left.left, ConditionReference)
    assert ir.left.left.span == ConditionSourceSpan(1, 12)
    assert isinstance(ir.left.right, ConditionLiteral)
    assert ir.left.right.span == ConditionSourceSpan(15, 17)
    assert isinstance(ir.right, ConditionReference)
    assert ir.right.span == ConditionSourceSpan(22, 27)


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

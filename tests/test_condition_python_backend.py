from __future__ import annotations

import ast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionLiteral,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
    condition_ir_to_python_ast,
    evaluate_condition_ir,
)


def test_condition_ir_emits_python_expression_ast_and_evaluates() -> None:
    ir = _temperature_gt_21()
    expression = condition_ir_to_python_ast(ir)

    assert isinstance(expression, ast.Expression)
    assert evaluate_condition_ir(ir, {"temperature": 22}) is True
    assert evaluate_condition_ir(ir, {"temperature": 20}) is False


def test_python_backend_rejects_missing_binding() -> None:
    with pytest.raises(ValueError, match="missing binding"):
        evaluate_condition_ir(_temperature_gt_21(), {})


@pytest.mark.property
@given(
    x=st.integers(min_value=-20, max_value=20),
    y=st.integers(min_value=-20, max_value=20),
    limit=st.integers(min_value=-40, max_value=40),
)
def test_python_backend_agrees_with_arithmetic_oracle(
    x: int,
    y: int,
    limit: int,
) -> None:
    span = ConditionSourceSpan(0, 12)
    ir = ConditionBinary(
        op=ConditionBinaryOp.LESS_THAN_OR_EQUAL,
        left=ConditionBinary(
            op=ConditionBinaryOp.ADD,
            left=ConditionReference(
                concept_id="ps:concept:x",
                source_name="x",
                value_kind=ConditionValueKind.NUMERIC,
                span=span,
            ),
            right=ConditionReference(
                concept_id="ps:concept:y",
                source_name="y",
                value_kind=ConditionValueKind.NUMERIC,
                span=span,
            ),
            span=span,
        ),
        right=ConditionLiteral(
            value=limit,
            value_kind=ConditionValueKind.NUMERIC,
            span=span,
        ),
        span=span,
    )

    assert evaluate_condition_ir(ir, {"x": x, "y": y}) == (x + y <= limit)


def _temperature_gt_21() -> ConditionBinary:
    span = ConditionSourceSpan(0, 16)
    return ConditionBinary(
        op=ConditionBinaryOp.GREATER_THAN,
        left=ConditionReference(
            concept_id="ps:concept:temperature",
            source_name="temperature",
            value_kind=ConditionValueKind.NUMERIC,
            span=span,
        ),
        right=ConditionLiteral(
            value=21,
            value_kind=ConditionValueKind.NUMERIC,
            span=span,
        ),
        span=span,
    )

from __future__ import annotations

import ast

from hypothesis import given
from hypothesis import strategies as st

from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
)
from propstore.core.conditions.estree_backend import (
    EstreeCallExpression,
    EstreeIdentifier,
    EstreeLiteral,
    EstreeLogicalExpression,
    EstreeMemberExpression,
    condition_ir_to_estree,
    evaluate_estree_expression,
)
from propstore.core.conditions.python_backend import evaluate_condition_ir
from propstore.core.id_types import ConceptId


SPAN = ConditionSourceSpan(0, 1)


def test_condition_ir_emits_typed_estree_without_raw_cel_or_python_ast() -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.AND,
        left=ConditionBinary(
            op=ConditionBinaryOp.GREATER_THAN,
            left=_numeric_ref("temperature"),
            right=ConditionLiteral(21, ConditionValueKind.NUMERIC, SPAN),
            span=SPAN,
        ),
        right=ConditionReference(
            concept_id=ConceptId("ps:concept:humid"),
            source_name="humid",
            value_kind=ConditionValueKind.BOOLEAN,
            span=SPAN,
        ),
        span=SPAN,
    )

    expression = condition_ir_to_estree(condition)

    assert isinstance(expression, EstreeLogicalExpression)
    assert expression.operator == "&&"
    assert "temperature > 21" not in repr(expression)
    assert not isinstance(expression, ast.AST)


def test_condition_membership_emits_array_includes_call() -> None:
    condition = ConditionMembership(
        element=ConditionReference(
            concept_id=ConceptId("ps:concept:phase"),
            source_name="phase",
            value_kind=ConditionValueKind.STRING,
            span=SPAN,
        ),
        options=(
            ConditionLiteral("draft", ConditionValueKind.STRING, SPAN),
            ConditionLiteral("review", ConditionValueKind.STRING, SPAN),
        ),
        span=SPAN,
    )

    expression = condition_ir_to_estree(condition)

    assert isinstance(expression, EstreeCallExpression)
    assert isinstance(expression.callee, EstreeMemberExpression)
    assert expression.callee.computed is False
    assert isinstance(expression.callee.property, EstreeIdentifier)
    assert expression.callee.property.name == "includes"
    assert isinstance(expression.arguments[0], EstreeIdentifier)
    assert expression.arguments[0].name == "phase"


def test_estree_evaluator_rejects_missing_binding() -> None:
    expression = condition_ir_to_estree(_numeric_ref("temperature"))

    try:
        evaluate_estree_expression(expression, {})
    except ValueError as exc:
        assert "missing binding: temperature" in str(exc)
    else:
        raise AssertionError("missing ESTree binding should raise")


@given(
    x=st.integers(min_value=-20, max_value=20),
    y=st.integers(min_value=-20, max_value=20),
    threshold=st.integers(min_value=-40, max_value=40),
)
def test_estree_backend_agrees_with_python_backend(
    x: int,
    y: int,
    threshold: int,
) -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
        left=ConditionBinary(
            op=ConditionBinaryOp.ADD,
            left=_numeric_ref("x"),
            right=ConditionBinary(
                op=ConditionBinaryOp.MULTIPLY,
                left=_numeric_ref("y"),
                right=ConditionLiteral(2, ConditionValueKind.NUMERIC, SPAN),
                span=SPAN,
            ),
            span=SPAN,
        ),
        right=ConditionLiteral(threshold, ConditionValueKind.NUMERIC, SPAN),
        span=SPAN,
    )
    bindings = {"x": x, "y": y}

    estree_expression = condition_ir_to_estree(condition)

    assert evaluate_estree_expression(estree_expression, bindings) == evaluate_condition_ir(
        condition,
        bindings,
    )


def test_estree_literal_evaluates_directly() -> None:
    expression = condition_ir_to_estree(
        ConditionLiteral(True, ConditionValueKind.BOOLEAN, SPAN)
    )

    assert expression == EstreeLiteral(True)
    assert evaluate_estree_expression(expression, {}) is True


def _numeric_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.NUMERIC,
        span=SPAN,
    )

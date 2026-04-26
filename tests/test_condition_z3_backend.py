from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
import z3

from propstore.core.conditions import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionSourceSpan,
    ConditionValueKind,
)
from propstore.core.conditions.python_backend import evaluate_condition_ir
from propstore.core.conditions.z3_backend import (
    condition_ir_to_z3,
    z3_bindings_for_values,
)
from propstore.core.id_types import ConceptId


SPAN = ConditionSourceSpan(0, 1)


def test_condition_ir_projects_decidable_fragment_to_z3() -> None:
    condition = ConditionBinary(
        op=ConditionBinaryOp.AND,
        left=ConditionBinary(
            op=ConditionBinaryOp.AND,
            left=ConditionBinary(
                op=ConditionBinaryOp.GREATER_THAN,
                left=_numeric_ref("temperature"),
                right=ConditionLiteral(21, ConditionValueKind.NUMERIC, SPAN),
                span=SPAN,
            ),
            right=_boolean_ref("humid"),
            span=SPAN,
        ),
        right=ConditionMembership(
            element=_string_ref("phase"),
            options=(
                ConditionLiteral("draft", ConditionValueKind.STRING, SPAN),
                ConditionLiteral("review", ConditionValueKind.STRING, SPAN),
            ),
            span=SPAN,
        ),
        span=SPAN,
    )

    expression = condition_ir_to_z3(condition)
    solver = z3.Solver()
    solver.add(*z3_bindings_for_values(condition, {
        "temperature": 22,
        "humid": True,
        "phase": "draft",
    }))
    solver.add(expression)

    assert solver.check() == z3.sat


def test_condition_choice_projects_to_z3_if_expression() -> None:
    condition = ConditionChoice(
        condition=_boolean_ref("enabled"),
        when_true=ConditionBinary(
            op=ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
            left=_numeric_ref("score"),
            right=ConditionLiteral(10, ConditionValueKind.NUMERIC, SPAN),
            span=SPAN,
        ),
        when_false=ConditionLiteral(True, ConditionValueKind.BOOLEAN, SPAN),
        span=SPAN,
    )
    solver = z3.Solver()
    solver.add(*z3_bindings_for_values(condition, {"enabled": True, "score": 9}))
    solver.add(condition_ir_to_z3(condition))

    assert solver.check() == z3.unsat


def test_z3_binding_projection_rejects_missing_binding() -> None:
    try:
        z3_bindings_for_values(_numeric_ref("temperature"), {})
    except ValueError as exc:
        assert "missing binding: temperature" in str(exc)
    else:
        raise AssertionError("missing Z3 binding should raise")


def test_z3_binding_projection_rejects_boolean_as_numeric() -> None:
    try:
        z3_bindings_for_values(_numeric_ref("temperature"), {"temperature": True})
    except TypeError as exc:
        assert "expected numeric binding" in str(exc)
    else:
        raise AssertionError("boolean numeric binding should raise")


@given(
    x=st.integers(min_value=-20, max_value=20),
    y=st.integers(min_value=-20, max_value=20),
    threshold=st.integers(min_value=-40, max_value=40),
)
def test_z3_backend_agrees_with_python_backend(
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
    expected = bool(evaluate_condition_ir(condition, bindings))

    solver = z3.Solver()
    solver.add(*z3_bindings_for_values(condition, bindings))
    solver.add(condition_ir_to_z3(condition) != z3.BoolVal(expected))

    assert solver.check() == z3.unsat


def _numeric_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.NUMERIC,
        span=SPAN,
    )


def _boolean_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.BOOLEAN,
        span=SPAN,
    )


def _string_ref(name: str) -> ConditionReference:
    return ConditionReference(
        concept_id=ConceptId(f"ps:concept:{name}"),
        source_name=name,
        value_kind=ConditionValueKind.STRING,
        span=SPAN,
    )

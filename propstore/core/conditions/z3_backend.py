"""Z3 backend for semantic ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import z3

from propstore.core.conditions.ir import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionIR,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionUnary,
    ConditionUnaryOp,
    ConditionValueKind,
)


@dataclass(frozen=True)
class _Projection:
    term: Any
    guards: tuple[Any, ...] = ()


def condition_ir_to_z3(condition: ConditionIR) -> Any:
    projection = _project(condition)
    if projection.guards and _is_boolean_term(projection.term):
        return z3.And(*projection.guards, projection.term)
    return projection.term


def z3_bindings_for_values(
    condition: ConditionIR,
    bindings: Mapping[str, object],
) -> tuple[Any, ...]:
    references = _reference_kinds(condition)
    constraints: list[Any] = []
    for name in sorted(references):
        if name not in bindings:
            raise ValueError(f"missing binding: {name}")
        constraints.append(_binding_constraint(name, references[name], bindings[name]))
    return tuple(constraints)


def _project(condition: ConditionIR) -> _Projection:
    if isinstance(condition, ConditionLiteral):
        return _project_literal(condition)
    if isinstance(condition, ConditionReference):
        return _Projection(_reference_term(condition))
    if isinstance(condition, ConditionUnary):
        operand = _project(condition.operand)
        if condition.op == ConditionUnaryOp.NOT:
            return _Projection(z3.Not(operand.term), operand.guards)
        if condition.op == ConditionUnaryOp.NEGATE:
            return _Projection(-operand.term, operand.guards)
        raise ValueError(f"unsupported unary condition op: {condition.op}")
    if isinstance(condition, ConditionBinary):
        return _project_binary(condition)
    if isinstance(condition, ConditionMembership):
        return _project_membership(condition)
    if isinstance(condition, ConditionChoice):
        return _project_choice(condition)
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _project_literal(condition: ConditionLiteral) -> _Projection:
    if condition.value_kind == ConditionValueKind.BOOLEAN and isinstance(condition.value, bool):
        return _Projection(z3.BoolVal(condition.value))
    if condition.value_kind == ConditionValueKind.NUMERIC and isinstance(condition.value, int | float):
        if isinstance(condition.value, bool):
            raise TypeError("boolean literal cannot project as numeric Z3 value")
        return _Projection(z3.RealVal(condition.value))
    if condition.value_kind == ConditionValueKind.STRING and isinstance(condition.value, str):
        return _Projection(z3.StringVal(condition.value))
    raise TypeError(f"unsupported ConditionIR literal for Z3: {condition.value!r}")


def _reference_term(condition: ConditionReference) -> Any:
    if condition.value_kind == ConditionValueKind.BOOLEAN:
        return z3.Bool(condition.source_name)
    if condition.value_kind == ConditionValueKind.NUMERIC:
        return z3.Real(condition.source_name)
    if condition.value_kind == ConditionValueKind.STRING:
        return z3.String(condition.source_name)
    raise ValueError(f"unsupported ConditionIR reference kind for Z3: {condition.value_kind}")


def _project_binary(condition: ConditionBinary) -> _Projection:
    left = _project(condition.left)
    right = _project(condition.right)
    guards = left.guards + right.guards

    if condition.op == ConditionBinaryOp.AND:
        return _Projection(z3.And(left.term, right.term), guards)
    if condition.op == ConditionBinaryOp.OR:
        return _Projection(z3.Or(left.term, right.term), guards)
    if condition.op == ConditionBinaryOp.EQUAL:
        return _Projection(left.term == right.term, guards)
    if condition.op == ConditionBinaryOp.NOT_EQUAL:
        return _Projection(left.term != right.term, guards)
    if condition.op == ConditionBinaryOp.LESS_THAN:
        return _Projection(left.term < right.term, guards)
    if condition.op == ConditionBinaryOp.LESS_THAN_OR_EQUAL:
        return _Projection(left.term <= right.term, guards)
    if condition.op == ConditionBinaryOp.GREATER_THAN:
        return _Projection(left.term > right.term, guards)
    if condition.op == ConditionBinaryOp.GREATER_THAN_OR_EQUAL:
        return _Projection(left.term >= right.term, guards)
    if condition.op == ConditionBinaryOp.ADD:
        return _Projection(left.term + right.term, guards)
    if condition.op == ConditionBinaryOp.SUBTRACT:
        return _Projection(left.term - right.term, guards)
    if condition.op == ConditionBinaryOp.MULTIPLY:
        return _Projection(left.term * right.term, guards)
    if condition.op == ConditionBinaryOp.DIVIDE:
        return _Projection(
            left.term / right.term,
            guards + (right.term != z3.RealVal(0),),
        )
    raise ValueError(f"unsupported binary condition op: {condition.op}")


def _project_membership(condition: ConditionMembership) -> _Projection:
    element = _project(condition.element)
    options = tuple(_project(option) for option in condition.options)
    guards = element.guards + tuple(guard for option in options for guard in option.guards)
    clauses = tuple(element.term == option.term for option in options)
    if not clauses:
        return _Projection(z3.BoolVal(False), guards)
    if len(clauses) == 1:
        return _Projection(clauses[0], guards)
    return _Projection(z3.Or(*clauses), guards)


def _project_choice(condition: ConditionChoice) -> _Projection:
    test = _project(condition.condition)
    when_true = _project(condition.when_true)
    when_false = _project(condition.when_false)
    return _Projection(
        z3.If(test.term, when_true.term, when_false.term),
        test.guards + when_true.guards + when_false.guards,
    )


def _is_boolean_term(term: Any) -> bool:
    return bool(z3.is_bool(term))


def _reference_kinds(condition: ConditionIR) -> dict[str, ConditionValueKind]:
    references: dict[str, ConditionValueKind] = {}
    _collect_reference_kinds(condition, references)
    return references


def _collect_reference_kinds(
    condition: ConditionIR,
    references: dict[str, ConditionValueKind],
) -> None:
    if isinstance(condition, ConditionReference):
        existing = references.get(condition.source_name)
        if existing is not None and existing != condition.value_kind:
            raise ValueError(f"conflicting ConditionIR kinds for binding: {condition.source_name}")
        references[condition.source_name] = condition.value_kind
        return
    if isinstance(condition, ConditionLiteral):
        return
    if isinstance(condition, ConditionUnary):
        _collect_reference_kinds(condition.operand, references)
        return
    if isinstance(condition, ConditionBinary):
        _collect_reference_kinds(condition.left, references)
        _collect_reference_kinds(condition.right, references)
        return
    if isinstance(condition, ConditionMembership):
        _collect_reference_kinds(condition.element, references)
        for option in condition.options:
            _collect_reference_kinds(option, references)
        return
    if isinstance(condition, ConditionChoice):
        _collect_reference_kinds(condition.condition, references)
        _collect_reference_kinds(condition.when_true, references)
        _collect_reference_kinds(condition.when_false, references)
        return
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _binding_constraint(
    name: str,
    value_kind: ConditionValueKind,
    value: object,
) -> Any:
    if value_kind == ConditionValueKind.NUMERIC:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"expected numeric binding for {name}")
        return z3.Real(name) == z3.RealVal(value)
    if value_kind == ConditionValueKind.BOOLEAN:
        if not isinstance(value, bool):
            raise TypeError(f"expected boolean binding for {name}")
        return z3.Bool(name) == z3.BoolVal(value)
    if value_kind == ConditionValueKind.STRING:
        if not isinstance(value, str):
            raise TypeError(f"expected string binding for {name}")
        return z3.String(name) == z3.StringVal(value)
    raise ValueError(f"unsupported ConditionIR binding kind for {name}: {value_kind}")

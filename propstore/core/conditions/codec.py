"""Versioned JSON encoding for semantic ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from propstore.core.conditions.ir import (
    ConditionBinary,
    ConditionBinaryOp,
    ConditionChoice,
    ConditionIR,
    ConditionLiteral,
    ConditionMembership,
    ConditionReference,
    ConditionSourceSpan,
    ConditionUnary,
    ConditionUnaryOp,
    ConditionValueKind,
)


CONDITION_IR_JSON_VERSION = 1


def condition_ir_to_json(condition: ConditionIR) -> dict[str, Any]:
    if isinstance(condition, ConditionLiteral):
        return {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "literal",
            "value": condition.value,
            "value_kind": condition.value_kind.value,
            "span": _span_to_json(condition.span),
        }
    if isinstance(condition, ConditionReference):
        encoded: dict[str, Any] = {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "reference",
            "concept_id": str(condition.concept_id),
            "source_name": condition.source_name,
            "value_kind": condition.value_kind.value,
            "span": _span_to_json(condition.span),
        }
        if condition.category_values:
            encoded["category_values"] = list(condition.category_values)
        if condition.category_extensible is not None:
            encoded["category_extensible"] = condition.category_extensible
        return encoded
    if isinstance(condition, ConditionUnary):
        return {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "unary",
            "op": condition.op.value,
            "operand": condition_ir_to_json(condition.operand),
            "span": _span_to_json(condition.span),
        }
    if isinstance(condition, ConditionBinary):
        return {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "binary",
            "op": condition.op.value,
            "left": condition_ir_to_json(condition.left),
            "right": condition_ir_to_json(condition.right),
            "span": _span_to_json(condition.span),
        }
    if isinstance(condition, ConditionMembership):
        return {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "membership",
            "element": condition_ir_to_json(condition.element),
            "options": [condition_ir_to_json(option) for option in condition.options],
            "span": _span_to_json(condition.span),
        }
    if isinstance(condition, ConditionChoice):
        return {
            "version": CONDITION_IR_JSON_VERSION,
            "node": "choice",
            "condition": condition_ir_to_json(condition.condition),
            "when_true": condition_ir_to_json(condition.when_true),
            "when_false": condition_ir_to_json(condition.when_false),
            "span": _span_to_json(condition.span),
        }
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _span_to_json(span: ConditionSourceSpan) -> list[int]:
    return [span.start, span.end]


def _span_from_json(value: object) -> ConditionSourceSpan:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError("ConditionIR span must be a two-item sequence")
    start, end = value
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("ConditionIR span entries must be integers")
    return ConditionSourceSpan(start, end)


def _string_sequence(value: object) -> tuple[str, ...]:
    result: list[str] = []
    for item in _sequence(value):
        if not isinstance(item, str):
            raise ValueError("ConditionIR string sequence entry must be a string")
        result.append(item)
    return tuple(result)


def _literal_value(value: object) -> bool | int | float | str:
    if isinstance(value, bool | int | float | str):
        return value
    raise ValueError("ConditionIR literal value must be a scalar")


def _value_kind(value: object) -> ConditionValueKind:
    try:
        return ConditionValueKind(value)
    except ValueError as exc:
        raise ValueError(f"unsupported ConditionIR value kind: {value!r}") from exc


def _unary_op(value: object) -> ConditionUnaryOp:
    try:
        return ConditionUnaryOp(value)
    except ValueError as exc:
        raise ValueError(f"unsupported ConditionIR unary op: {value!r}") from exc


def _binary_op(value: object) -> ConditionBinaryOp:
    try:
        return ConditionBinaryOp(value)
    except ValueError as exc:
        raise ValueError(f"unsupported ConditionIR binary op: {value!r}") from exc

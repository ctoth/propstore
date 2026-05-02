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


def condition_ir_from_json(payload: Mapping[str, Any]) -> ConditionIR:
    version = payload.get("version")
    if version != CONDITION_IR_JSON_VERSION:
        raise ValueError(f"unsupported ConditionIR encoding version: {version!r}")
    node = payload.get("node")
    if node == "literal":
        return ConditionLiteral(
            value=_literal_value(payload.get("value")),
            value_kind=_value_kind(payload.get("value_kind")),
            span=_span_from_json(payload.get("span")),
        )
    if node == "reference":
        return ConditionReference(
            concept_id=_required_str(payload, "concept_id"),
            source_name=_required_str(payload, "source_name"),
            value_kind=_value_kind(payload.get("value_kind")),
            span=_span_from_json(payload.get("span")),
            category_values=tuple(
                _string_sequence(payload.get("category_values", ()))
            ),
            category_extensible=(
                None
                if "category_extensible" not in payload
                else bool(payload["category_extensible"])
            ),
        )
    if node == "unary":
        return ConditionUnary(
            op=_unary_op(payload.get("op")),
            operand=condition_ir_from_json(_mapping(payload.get("operand"))),
            span=_span_from_json(payload.get("span")),
        )
    if node == "binary":
        return ConditionBinary(
            op=_binary_op(payload.get("op")),
            left=condition_ir_from_json(_mapping(payload.get("left"))),
            right=condition_ir_from_json(_mapping(payload.get("right"))),
            span=_span_from_json(payload.get("span")),
        )
    if node == "membership":
        return ConditionMembership(
            element=condition_ir_from_json(_mapping(payload.get("element"))),
            options=tuple(
                condition_ir_from_json(_mapping(option))
                for option in _sequence(payload.get("options"))
            ),
            span=_span_from_json(payload.get("span")),
        )
    if node == "choice":
        return ConditionChoice(
            condition=condition_ir_from_json(_mapping(payload.get("condition"))),
            when_true=condition_ir_from_json(_mapping(payload.get("when_true"))),
            when_false=condition_ir_from_json(_mapping(payload.get("when_false"))),
            span=_span_from_json(payload.get("span")),
        )
    raise ValueError(f"unsupported ConditionIR node tag: {node!r}")


def _span_to_json(span: ConditionSourceSpan) -> list[int]:
    return [span.start, span.end]


def _span_from_json(value: object) -> ConditionSourceSpan:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError("ConditionIR span must be a two-item sequence")
    start, end = value
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("ConditionIR span entries must be integers")
    return ConditionSourceSpan(start, end)


def _mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("ConditionIR nested payload must be a mapping")
    return cast(Mapping[str, Any], value)


def _sequence(value: object) -> tuple[object, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError("ConditionIR sequence payload must be a sequence")
    return tuple(value)


def _string_sequence(value: object) -> tuple[str, ...]:
    result: list[str] = []
    for item in _sequence(value):
        if not isinstance(item, str):
            raise ValueError("ConditionIR string sequence entry must be a string")
        result.append(item)
    return tuple(result)


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"ConditionIR field {key!r} must be a string")
    return value


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

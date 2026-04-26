"""ESTree backend for semantic ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias

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
)


@dataclass(frozen=True)
class EstreeIdentifier:
    name: str


@dataclass(frozen=True)
class EstreeLiteral:
    value: object


@dataclass(frozen=True)
class EstreeUnaryExpression:
    operator: str
    argument: EstreeExpression
    prefix: bool = True


@dataclass(frozen=True)
class EstreeBinaryExpression:
    operator: str
    left: EstreeExpression
    right: EstreeExpression


@dataclass(frozen=True)
class EstreeLogicalExpression:
    operator: str
    left: EstreeExpression
    right: EstreeExpression


@dataclass(frozen=True)
class EstreeArrayExpression:
    elements: tuple[EstreeExpression, ...]


@dataclass(frozen=True)
class EstreeMemberExpression:
    object: EstreeExpression
    property: EstreeExpression
    computed: bool


@dataclass(frozen=True)
class EstreeCallExpression:
    callee: EstreeExpression
    arguments: tuple[EstreeExpression, ...]


@dataclass(frozen=True)
class EstreeConditionalExpression:
    test: EstreeExpression
    consequent: EstreeExpression
    alternate: EstreeExpression


EstreeExpression: TypeAlias = (
    EstreeIdentifier
    | EstreeLiteral
    | EstreeUnaryExpression
    | EstreeBinaryExpression
    | EstreeLogicalExpression
    | EstreeArrayExpression
    | EstreeMemberExpression
    | EstreeCallExpression
    | EstreeConditionalExpression
)


def condition_ir_to_estree(condition: ConditionIR) -> EstreeExpression:
    if isinstance(condition, ConditionLiteral):
        return EstreeLiteral(condition.value)
    if isinstance(condition, ConditionReference):
        return EstreeIdentifier(condition.source_name)
    if isinstance(condition, ConditionUnary):
        return EstreeUnaryExpression(
            operator=_unary_operator(condition.op),
            argument=condition_ir_to_estree(condition.operand),
        )
    if isinstance(condition, ConditionBinary):
        if condition.op in _LOGICAL_OPS:
            return EstreeLogicalExpression(
                operator=_logical_operator(condition.op),
                left=condition_ir_to_estree(condition.left),
                right=condition_ir_to_estree(condition.right),
            )
        return EstreeBinaryExpression(
            operator=_binary_operator(condition.op),
            left=condition_ir_to_estree(condition.left),
            right=condition_ir_to_estree(condition.right),
        )
    if isinstance(condition, ConditionMembership):
        return EstreeCallExpression(
            callee=EstreeMemberExpression(
                object=EstreeArrayExpression(
                    tuple(condition_ir_to_estree(option) for option in condition.options)
                ),
                property=EstreeIdentifier("includes"),
                computed=False,
            ),
            arguments=(condition_ir_to_estree(condition.element),),
        )
    if isinstance(condition, ConditionChoice):
        return EstreeConditionalExpression(
            test=condition_ir_to_estree(condition.condition),
            consequent=condition_ir_to_estree(condition.when_true),
            alternate=condition_ir_to_estree(condition.when_false),
        )
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def evaluate_estree_expression(
    expression: EstreeExpression,
    bindings: Mapping[str, object],
) -> object:
    if isinstance(expression, EstreeLiteral):
        return expression.value
    if isinstance(expression, EstreeIdentifier):
        if expression.name not in bindings:
            raise ValueError(f"missing binding: {expression.name}")
        return bindings[expression.name]
    if isinstance(expression, EstreeUnaryExpression):
        argument = evaluate_estree_expression(expression.argument, bindings)
        if expression.operator == "!":
            return not bool(argument)
        if expression.operator == "-":
            return -_numeric_value(argument)
        raise ValueError(f"unsupported ESTree unary operator: {expression.operator}")
    if isinstance(expression, EstreeLogicalExpression):
        left = evaluate_estree_expression(expression.left, bindings)
        if expression.operator == "&&":
            return bool(left) and bool(evaluate_estree_expression(expression.right, bindings))
        if expression.operator == "||":
            return bool(left) or bool(evaluate_estree_expression(expression.right, bindings))
        raise ValueError(f"unsupported ESTree logical operator: {expression.operator}")
    if isinstance(expression, EstreeBinaryExpression):
        return _evaluate_binary_expression(expression, bindings)
    if isinstance(expression, EstreeArrayExpression):
        return tuple(evaluate_estree_expression(element, bindings) for element in expression.elements)
    if isinstance(expression, EstreeMemberExpression):
        return _evaluate_member_expression(expression, bindings)
    if isinstance(expression, EstreeCallExpression):
        return _evaluate_call_expression(expression, bindings)
    if isinstance(expression, EstreeConditionalExpression):
        test = evaluate_estree_expression(expression.test, bindings)
        branch = expression.consequent if bool(test) else expression.alternate
        return evaluate_estree_expression(branch, bindings)
    raise TypeError(f"unsupported ESTree expression: {type(expression).__name__}")


def _evaluate_binary_expression(
    expression: EstreeBinaryExpression,
    bindings: Mapping[str, object],
) -> object:
    left = evaluate_estree_expression(expression.left, bindings)
    right = evaluate_estree_expression(expression.right, bindings)
    if expression.operator == "===":
        return left == right
    if expression.operator == "!==":
        return left != right
    if expression.operator == "<":
        return left < right  # type: ignore[operator]
    if expression.operator == "<=":
        return left <= right  # type: ignore[operator]
    if expression.operator == ">":
        return left > right  # type: ignore[operator]
    if expression.operator == ">=":
        return left >= right  # type: ignore[operator]
    if expression.operator == "+":
        return _numeric_value(left) + _numeric_value(right)
    if expression.operator == "-":
        return _numeric_value(left) - _numeric_value(right)
    if expression.operator == "*":
        return _numeric_value(left) * _numeric_value(right)
    if expression.operator == "/":
        return _numeric_value(left) / _numeric_value(right)
    raise ValueError(f"unsupported ESTree binary operator: {expression.operator}")


def _evaluate_member_expression(
    expression: EstreeMemberExpression,
    bindings: Mapping[str, object],
) -> tuple[object, str]:
    target = evaluate_estree_expression(expression.object, bindings)
    if expression.computed:
        raise ValueError("computed ESTree members are not supported")
    if not isinstance(expression.property, EstreeIdentifier):
        raise ValueError("non-identifier ESTree member properties are not supported")
    return target, expression.property.name


def _evaluate_call_expression(
    expression: EstreeCallExpression,
    bindings: Mapping[str, object],
) -> object:
    if not isinstance(expression.callee, EstreeMemberExpression):
        raise ValueError("only ESTree member calls are supported")
    target, member_name = _evaluate_member_expression(expression.callee, bindings)
    if member_name == "includes":
        if len(expression.arguments) != 1:
            raise ValueError("Array.includes expects one argument")
        needle = evaluate_estree_expression(expression.arguments[0], bindings)
        if not isinstance(target, tuple):
            raise ValueError("Array.includes target must be an array expression")
        return needle in target
    raise ValueError(f"unsupported ESTree member call: {member_name}")


def _numeric_value(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"expected numeric ESTree value, got {type(value).__name__}")
    return value


def _unary_operator(op: ConditionUnaryOp) -> str:
    if op == ConditionUnaryOp.NOT:
        return "!"
    if op == ConditionUnaryOp.NEGATE:
        return "-"
    raise ValueError(f"unsupported unary condition op: {op}")


_LOGICAL_OPS = frozenset((ConditionBinaryOp.AND, ConditionBinaryOp.OR))


def _logical_operator(op: ConditionBinaryOp) -> str:
    if op == ConditionBinaryOp.AND:
        return "&&"
    if op == ConditionBinaryOp.OR:
        return "||"
    raise ValueError(f"unsupported logical condition op: {op}")


def _binary_operator(op: ConditionBinaryOp) -> str:
    if op == ConditionBinaryOp.EQUAL:
        return "==="
    if op == ConditionBinaryOp.NOT_EQUAL:
        return "!=="
    if op == ConditionBinaryOp.LESS_THAN:
        return "<"
    if op == ConditionBinaryOp.LESS_THAN_OR_EQUAL:
        return "<="
    if op == ConditionBinaryOp.GREATER_THAN:
        return ">"
    if op == ConditionBinaryOp.GREATER_THAN_OR_EQUAL:
        return ">="
    if op == ConditionBinaryOp.ADD:
        return "+"
    if op == ConditionBinaryOp.SUBTRACT:
        return "-"
    if op == ConditionBinaryOp.MULTIPLY:
        return "*"
    if op == ConditionBinaryOp.DIVIDE:
        return "/"
    raise ValueError(f"unsupported binary condition op: {op}")

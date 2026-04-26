"""Parameterized SQL fragment backend for semantic ConditionIR."""

from __future__ import annotations

from dataclasses import dataclass

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
class SqlConditionFragment:
    sql: str
    parameters: tuple[object, ...] = ()


def condition_ir_to_sql(condition: ConditionIR) -> SqlConditionFragment:
    if isinstance(condition, ConditionLiteral):
        return SqlConditionFragment("?", (condition.value,))
    if isinstance(condition, ConditionReference):
        return SqlConditionFragment(_quote_identifier(condition.source_name))
    if isinstance(condition, ConditionUnary):
        operand = condition_ir_to_sql(condition.operand)
        if condition.op == ConditionUnaryOp.NOT:
            return SqlConditionFragment(
                f"(NOT {operand.sql})",
                operand.parameters,
            )
        if condition.op == ConditionUnaryOp.NEGATE:
            return SqlConditionFragment(
                f"(-{operand.sql})",
                operand.parameters,
            )
        raise ValueError(f"unsupported unary condition op for SQL: {condition.op}")
    if isinstance(condition, ConditionBinary):
        return _condition_binary_to_sql(condition)
    if isinstance(condition, ConditionMembership):
        return _condition_membership_to_sql(condition)
    if isinstance(condition, ConditionChoice):
        raise ValueError("ConditionChoice cannot be projected to SQL")
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _condition_binary_to_sql(condition: ConditionBinary) -> SqlConditionFragment:
    left = condition_ir_to_sql(condition.left)
    right = condition_ir_to_sql(condition.right)
    return SqlConditionFragment(
        f"({left.sql} {_binary_operator(condition.op)} {right.sql})",
        left.parameters + right.parameters,
    )


def _condition_membership_to_sql(condition: ConditionMembership) -> SqlConditionFragment:
    element = condition_ir_to_sql(condition.element)
    if not condition.options:
        return SqlConditionFragment("(0 = 1)", element.parameters)
    options = tuple(condition_ir_to_sql(option) for option in condition.options)
    option_sql = ", ".join(option.sql for option in options)
    parameters = element.parameters + tuple(
        parameter
        for option in options
        for parameter in option.parameters
    )
    return SqlConditionFragment(
        f"({element.sql} IN ({option_sql}))",
        parameters,
    )


def _binary_operator(op: ConditionBinaryOp) -> str:
    if op == ConditionBinaryOp.AND:
        return "AND"
    if op == ConditionBinaryOp.OR:
        return "OR"
    if op == ConditionBinaryOp.EQUAL:
        return "="
    if op == ConditionBinaryOp.NOT_EQUAL:
        return "<>"
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
    raise ValueError(f"unsupported binary condition op for SQL: {op}")


def _quote_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'

"""Python AST backend for semantic ConditionIR."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import cast

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


def condition_ir_to_python_ast(condition: ConditionIR) -> ast.Expression:
    expression = ast.Expression(body=_to_expr(condition))
    return cast(ast.Expression, ast.fix_missing_locations(expression))


def evaluate_condition_ir(
    condition: ConditionIR,
    bindings: Mapping[str, object],
) -> object:
    missing = _reference_names(condition).difference(bindings.keys())
    if missing:
        raise ValueError(f"missing binding: {sorted(missing)[0]}")
    expression = condition_ir_to_python_ast(condition)
    compiled = compile(expression, "<condition-ir>", "eval")
    return eval(compiled, {"__builtins__": {}}, dict(bindings))


def _to_expr(condition: ConditionIR) -> ast.expr:
    if isinstance(condition, ConditionLiteral):
        return ast.Constant(value=condition.value)
    if isinstance(condition, ConditionReference):
        return ast.Name(id=condition.source_name, ctx=ast.Load())
    if isinstance(condition, ConditionUnary):
        return ast.UnaryOp(
            op=_unary_op(condition.op),
            operand=_to_expr(condition.operand),
        )
    if isinstance(condition, ConditionBinary):
        if condition.op in _BOOLEAN_OPS:
            return ast.BoolOp(
                op=_bool_op(condition.op),
                values=[_to_expr(condition.left), _to_expr(condition.right)],
            )
        if condition.op in _COMPARISON_OPS:
            return ast.Compare(
                left=_to_expr(condition.left),
                ops=[_comparison_op(condition.op)],
                comparators=[_to_expr(condition.right)],
            )
        return ast.BinOp(
            left=_to_expr(condition.left),
            op=_binary_op(condition.op),
            right=_to_expr(condition.right),
        )
    if isinstance(condition, ConditionMembership):
        return ast.Compare(
            left=_to_expr(condition.element),
            ops=[ast.In()],
            comparators=[
                ast.List(
                    elts=[_to_expr(option) for option in condition.options],
                    ctx=ast.Load(),
                )
            ],
        )
    if isinstance(condition, ConditionChoice):
        return ast.IfExp(
            test=_to_expr(condition.condition),
            body=_to_expr(condition.when_true),
            orelse=_to_expr(condition.when_false),
        )
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _reference_names(condition: ConditionIR) -> frozenset[str]:
    if isinstance(condition, ConditionReference):
        return frozenset((condition.source_name,))
    if isinstance(condition, ConditionLiteral):
        return frozenset()
    if isinstance(condition, ConditionUnary):
        return _reference_names(condition.operand)
    if isinstance(condition, ConditionBinary):
        return _reference_names(condition.left).union(_reference_names(condition.right))
    if isinstance(condition, ConditionMembership):
        names = set(_reference_names(condition.element))
        for option in condition.options:
            names.update(_reference_names(option))
        return frozenset(names)
    if isinstance(condition, ConditionChoice):
        return (
            _reference_names(condition.condition)
            .union(_reference_names(condition.when_true))
            .union(_reference_names(condition.when_false))
        )
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def _unary_op(op: ConditionUnaryOp) -> ast.unaryop:
    if op == ConditionUnaryOp.NOT:
        return ast.Not()
    if op == ConditionUnaryOp.NEGATE:
        return ast.USub()
    raise ValueError(f"unsupported unary condition op: {op}")


_BOOLEAN_OPS = frozenset((ConditionBinaryOp.AND, ConditionBinaryOp.OR))
_COMPARISON_OPS = frozenset((
    ConditionBinaryOp.EQUAL,
    ConditionBinaryOp.NOT_EQUAL,
    ConditionBinaryOp.LESS_THAN,
    ConditionBinaryOp.LESS_THAN_OR_EQUAL,
    ConditionBinaryOp.GREATER_THAN,
    ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
))


def _bool_op(op: ConditionBinaryOp) -> ast.boolop:
    if op == ConditionBinaryOp.AND:
        return ast.And()
    if op == ConditionBinaryOp.OR:
        return ast.Or()
    raise ValueError(f"unsupported boolean condition op: {op}")


def _comparison_op(op: ConditionBinaryOp) -> ast.cmpop:
    if op == ConditionBinaryOp.EQUAL:
        return ast.Eq()
    if op == ConditionBinaryOp.NOT_EQUAL:
        return ast.NotEq()
    if op == ConditionBinaryOp.LESS_THAN:
        return ast.Lt()
    if op == ConditionBinaryOp.LESS_THAN_OR_EQUAL:
        return ast.LtE()
    if op == ConditionBinaryOp.GREATER_THAN:
        return ast.Gt()
    if op == ConditionBinaryOp.GREATER_THAN_OR_EQUAL:
        return ast.GtE()
    raise ValueError(f"unsupported comparison condition op: {op}")


def _binary_op(op: ConditionBinaryOp) -> ast.operator:
    if op == ConditionBinaryOp.ADD:
        return ast.Add()
    if op == ConditionBinaryOp.SUBTRACT:
        return ast.Sub()
    if op == ConditionBinaryOp.MULTIPLY:
        return ast.Mult()
    if op == ConditionBinaryOp.DIVIDE:
        return ast.Div()
    raise ValueError(f"unsupported arithmetic condition op: {op}")

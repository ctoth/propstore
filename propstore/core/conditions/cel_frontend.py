"""CEL frontend adapter that lowers checked CEL source into ConditionIR.

cel-parser produces a proto-faithful AST where every operator is a
``Call(function="_+_", target=None, args=...)``. This module translates
that canonical form into propstore's ``ConditionIR`` (which uses bare
operator strings on ``ConditionBinaryOp`` / ``ConditionUnaryOp``).

Unsupported nodes (Select, CreateMap, CreateStruct, Comprehension, generic
Call, BytesLit, NullLit) raise ``TypeError`` with the source span. propstore
conditions can grow into these as needed; today they are out of scope.
"""

from __future__ import annotations

from collections.abc import Mapping

from cel_parser import (
    OP_ADD,
    OP_AND,
    OP_DIV,
    OP_EQ,
    OP_GE,
    OP_GT,
    OP_IN,
    OP_LE,
    OP_LT,
    OP_MUL,
    OP_NE,
    OP_NEG,
    OP_NOT,
    OP_OR,
    OP_SUB,
    OP_TERNARY,
    BoolLit,
    Call,
    CreateList,
    DoubleLit,
    Expr,
    Ident,
    IntLit,
    SourceSpan,
    StringLit,
    UintLit,
)

from propstore.cel_checker import (
    CheckedCelExpr,
    check_cel_expr,
)
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions.checked import CheckedCondition
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


def condition_ir_from_cel(
    source: str,
    registry: Mapping[str, ConceptInfo],
) -> ConditionIR:
    checked = check_cel_expr(source, registry)
    return _condition_ir_from_checked(checked, registry)


def check_condition_ir(
    source: str,
    registry: Mapping[str, ConceptInfo],
) -> CheckedCondition:
    checked = check_cel_expr(source, registry)
    return CheckedCondition(
        source=str(checked.source),
        ir=_condition_ir_from_checked(checked, registry),
        registry_fingerprint=str(checked.registry_fingerprint),
        warnings=tuple(warning.message for warning in checked.warnings),
    )


def _condition_ir_from_checked(
    checked: CheckedCelExpr,
    registry: Mapping[str, ConceptInfo],
) -> ConditionIR:
    return _lower_node(checked.ast, registry)


# Map cel-parser canonical function names to ConditionBinaryOp values.
_BINARY_OP_MAP: dict[str, ConditionBinaryOp] = {
    OP_ADD: ConditionBinaryOp.ADD,
    OP_SUB: ConditionBinaryOp.SUBTRACT,
    OP_MUL: ConditionBinaryOp.MULTIPLY,
    OP_DIV: ConditionBinaryOp.DIVIDE,
    OP_EQ: ConditionBinaryOp.EQUAL,
    OP_NE: ConditionBinaryOp.NOT_EQUAL,
    OP_LT: ConditionBinaryOp.LESS_THAN,
    OP_LE: ConditionBinaryOp.LESS_THAN_OR_EQUAL,
    OP_GT: ConditionBinaryOp.GREATER_THAN,
    OP_GE: ConditionBinaryOp.GREATER_THAN_OR_EQUAL,
    OP_AND: ConditionBinaryOp.AND,
    OP_OR: ConditionBinaryOp.OR,
}


def _lower_node(
    node: Expr,
    registry: Mapping[str, ConceptInfo],
    *,
    allow_string_literal: bool = False,
) -> ConditionIR:
    if isinstance(node, Ident):
        return _lower_name(node, registry)

    if isinstance(node, BoolLit):
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.BOOLEAN,
            span=_condition_span(node.span),
        )
    if isinstance(node, (IntLit, UintLit, DoubleLit)):
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.NUMERIC,
            span=_condition_span(node.span),
        )
    if isinstance(node, StringLit):
        if not allow_string_literal:
            raise TypeError(f"bare string literal cannot form ConditionIR at {node.span}")
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.STRING,
            span=_condition_span(node.span),
        )

    if isinstance(node, Call) and node.target is None:
        if node.function == OP_NOT and len(node.args) == 1:
            return ConditionUnary(
                op=ConditionUnaryOp.NOT,
                operand=_lower_node(node.args[0], registry),
                span=_condition_span(node.span),
            )
        if node.function == OP_NEG and len(node.args) == 1:
            return ConditionUnary(
                op=ConditionUnaryOp.NEGATE,
                operand=_lower_node(node.args[0], registry),
                span=_condition_span(node.span),
            )
        if node.function == OP_TERNARY and len(node.args) == 3:
            cond, then_branch, else_branch = node.args
            return ConditionChoice(
                condition=_lower_node(cond, registry),
                when_true=_lower_node(
                    then_branch,
                    registry,
                    allow_string_literal=allow_string_literal,
                ),
                when_false=_lower_node(
                    else_branch,
                    registry,
                    allow_string_literal=allow_string_literal,
                ),
                span=_condition_span(node.span),
            )
        if node.function == OP_IN and len(node.args) == 2:
            element, list_expr = node.args
            if not isinstance(list_expr, CreateList):
                raise TypeError(
                    f"unsupported 'in' rhs (expected list literal) at {node.span}"
                )
            return ConditionMembership(
                element=_lower_node(element, registry),
                options=tuple(
                    _lower_node(value, registry, allow_string_literal=True)
                    for value in list_expr.elements
                ),
                span=_condition_span(node.span),
            )
        if node.function in _BINARY_OP_MAP and len(node.args) == 2:
            left, right = node.args
            allow_child_strings = node.function in (OP_EQ, OP_NE)
            return ConditionBinary(
                op=_BINARY_OP_MAP[node.function],
                left=_lower_node(
                    left,
                    registry,
                    allow_string_literal=allow_child_strings,
                ),
                right=_lower_node(
                    right,
                    registry,
                    allow_string_literal=allow_child_strings,
                ),
                span=_condition_span(node.span),
            )

    raise TypeError(
        f"unsupported CEL AST node for ConditionIR: {type(node).__name__} "
        f"({getattr(node, 'function', '')!r}) at {node.span}"
    )


def _lower_name(
    node: Ident,
    registry: Mapping[str, ConceptInfo],
) -> ConditionReference:
    info = registry.get(node.name)
    if info is None:
        raise ValueError(f"Undefined concept: {node.name}")
    if info.kind == KindType.STRUCTURAL:
        raise ValueError(
            f"Structural concept '{node.name}' cannot appear in ConditionIR"
        )
    return ConditionReference(
        concept_id=info.id,
        source_name=node.name,
        value_kind=_value_kind(info.kind),
        span=_condition_span(node.span),
        category_values=tuple(info.category_values),
        category_extensible=(
            info.category_extensible if info.kind == KindType.CATEGORY else None
        ),
    )


def _condition_span(span: SourceSpan) -> ConditionSourceSpan:
    return ConditionSourceSpan(span.start, span.end)


def _value_kind(kind: KindType) -> ConditionValueKind:
    if kind == KindType.QUANTITY:
        return ConditionValueKind.NUMERIC
    if kind == KindType.TIMEPOINT:
        return ConditionValueKind.TIMEPOINT
    if kind == KindType.CATEGORY:
        return ConditionValueKind.STRING
    if kind == KindType.BOOLEAN:
        return ConditionValueKind.BOOLEAN
    raise ValueError(
        f"Structural concept kind cannot lower to ConditionIR: {kind.value}"
    )

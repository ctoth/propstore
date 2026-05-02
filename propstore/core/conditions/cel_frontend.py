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
from dataclasses import dataclass
from enum import Enum

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
    OP_MOD,
    OP_MUL,
    OP_NE,
    OP_NEG,
    OP_NOT,
    OP_OR,
    OP_SUB,
    OP_TERNARY,
    BoolLit,
    BytesLit,
    Call,
    CreateList,
    DoubleLit,
    Expr,
    Ident,
    IntLit,
    NullLit,
    ParseError,
    SourceSpan,
    StringLit,
    UintLit,
    parse,
)

from propstore.cel_types import CelExpr, to_cel_expr
from propstore.core.conditions.registry import (
    ConceptInfo,
    KindType,
    condition_registry_fingerprint,
)
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


@dataclass
class CelError:
    expression: str
    message: str
    is_warning: bool = False

    def __str__(self) -> str:
        prefix = "WARNING" if self.is_warning else "ERROR"
        return f"{prefix}: {self.message} in expression: {self.expression}"


class ExprType(Enum):
    NUMERIC = "numeric"
    STRING = "string"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


ARITHMETIC_FUNCTIONS = {OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD}
ORDERING_FUNCTIONS = {OP_LT, OP_LE, OP_GT, OP_GE}
EQUALITY_FUNCTIONS = {OP_EQ, OP_NE}
LOGICAL_FUNCTIONS = {OP_AND, OP_OR}

_DISALLOWED_KIND_USAGE: dict[str, dict[KindType, str]] = {
    "arithmetic": {
        KindType.CATEGORY: "Category concept '{name}' cannot appear in arithmetic",
        KindType.BOOLEAN: "Boolean concept '{name}' cannot appear in arithmetic",
    },
    "ordering comparison": {
        KindType.CATEGORY: "Category concept '{name}' cannot appear in ordering comparison",
        KindType.BOOLEAN: "Boolean concept '{name}' cannot appear in ordering comparison",
    },
}


def check_cel_expression(
    expr: str | CelExpr,
    registry: Mapping[str, ConceptInfo],
) -> list[CelError]:
    """Type-check a CEL expression against the concept registry."""
    source = to_cel_expr(expr)
    errors: list[CelError] = []

    try:
        ast = parse(str(source))
    except ParseError as exc:
        errors.append(CelError(str(source), f"Parse error: {exc}"))
        return errors

    _check_node(ast, str(source), registry, errors)
    return errors


def _is_unary_call(node: Expr, function: str) -> bool:
    return (
        isinstance(node, Call)
        and node.target is None
        and node.function == function
        and len(node.args) == 1
    )


def _is_in_call(node: Expr) -> bool:
    return (
        isinstance(node, Call)
        and node.target is None
        and node.function == OP_IN
        and len(node.args) == 2
    )


def _is_ternary_call(node: Expr) -> bool:
    return (
        isinstance(node, Call)
        and node.target is None
        and node.function == OP_TERNARY
        and len(node.args) == 3
    )


def _resolve_type(
    node: Expr,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    if isinstance(node, (IntLit, DoubleLit, UintLit)):
        return ExprType.NUMERIC
    if isinstance(node, StringLit):
        return ExprType.STRING
    if isinstance(node, BytesLit):
        return ExprType.STRING
    if isinstance(node, BoolLit):
        return ExprType.BOOLEAN
    if isinstance(node, NullLit):
        return ExprType.UNKNOWN

    if isinstance(node, Ident):
        info = registry.get(node.name)
        if info is None:
            errors.append(CelError(expr, f"Undefined concept: '{node.name}'"))
            return ExprType.UNKNOWN
        if info.kind == KindType.STRUCTURAL:
            errors.append(
                CelError(
                    expr,
                    f"Structural concept '{node.name}' cannot appear in CEL expressions",
                )
            )
            return ExprType.UNKNOWN
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            return ExprType.NUMERIC
        if info.kind == KindType.CATEGORY:
            return ExprType.STRING
        if info.kind == KindType.BOOLEAN:
            return ExprType.BOOLEAN
        return ExprType.UNKNOWN

    if _is_unary_call(node, OP_NOT):
        assert isinstance(node, Call)
        inner = _resolve_type(node.args[0], expr, registry, errors)
        if inner == ExprType.UNKNOWN:
            return ExprType.UNKNOWN
        if inner != ExprType.BOOLEAN:
            errors.append(
                CelError(expr, f"Operand of '!' must be boolean, got {inner.value}")
            )
            return ExprType.UNKNOWN
        return ExprType.BOOLEAN
    if _is_unary_call(node, OP_NEG):
        assert isinstance(node, Call)
        inner = _resolve_type(node.args[0], expr, registry, errors)
        if inner == ExprType.UNKNOWN:
            return ExprType.UNKNOWN
        if inner != ExprType.NUMERIC:
            errors.append(
                CelError(
                    expr,
                    f"Operand of unary '-' must be numeric, got {inner.value}",
                )
            )
            return ExprType.UNKNOWN
        return ExprType.NUMERIC

    if _is_in_call(node):
        assert isinstance(node, Call)
        return _check_in_call(node, expr, registry, errors)

    if _is_ternary_call(node):
        assert isinstance(node, Call)
        return _check_ternary_call(node, expr, registry, errors)

    if isinstance(node, Call) and node.target is None and len(node.args) == 2:
        if node.function in LOGICAL_FUNCTIONS:
            return _check_logical(node, expr, registry, errors)
        if node.function in ARITHMETIC_FUNCTIONS:
            return _check_arithmetic(node, expr, registry, errors)
        if node.function in ORDERING_FUNCTIONS:
            return _check_ordering(node, expr, registry, errors)
        if node.function in EQUALITY_FUNCTIONS:
            return _check_equality(node, expr, registry, errors)

    return ExprType.UNKNOWN


def _check_logical(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    left, right = node.args
    left_type = _resolve_type(left, expr, registry, errors)
    right_type = _resolve_type(right, expr, registry, errors)
    op = _short_op(node.function)
    bool_compatible = {ExprType.BOOLEAN, ExprType.UNKNOWN}
    if left_type not in bool_compatible:
        errors.append(
            CelError(expr, f"Left operand of '{op}' must be boolean, got {left_type.value}")
        )
    if right_type not in bool_compatible:
        errors.append(
            CelError(
                expr, f"Right operand of '{op}' must be boolean, got {right_type.value}"
            )
        )
    return ExprType.BOOLEAN


def _check_arithmetic(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    left, right = node.args
    _resolve_type(left, expr, registry, errors)
    _resolve_type(right, expr, registry, errors)
    _check_disallowed_kind_usage(left, expr, registry, errors, operation_class="arithmetic")
    _check_disallowed_kind_usage(right, expr, registry, errors, operation_class="arithmetic")
    return ExprType.NUMERIC


def _check_ordering(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    left, right = node.args
    left_type = _resolve_type(left, expr, registry, errors)
    right_type = _resolve_type(right, expr, registry, errors)
    _check_disallowed_kind_usage(
        left, expr, registry, errors, operation_class="ordering comparison"
    )
    _check_disallowed_kind_usage(
        right, expr, registry, errors, operation_class="ordering comparison"
    )
    _check_comparison_type_mismatch(
        left, right, left_type, right_type, expr, registry, errors
    )
    return ExprType.BOOLEAN


def _check_equality(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    left, right = node.args
    left_type = _resolve_type(left, expr, registry, errors)
    right_type = _resolve_type(right, expr, registry, errors)
    _check_comparison_type_mismatch(
        left, right, left_type, right_type, expr, registry, errors
    )
    _check_category_value(left, right, expr, registry, errors)
    _check_category_value(right, left, expr, registry, errors)
    return ExprType.BOOLEAN


def _check_in_call(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    element, list_expr = node.args
    _resolve_type(element, expr, registry, errors)
    if not isinstance(list_expr, CreateList):
        errors.append(CelError(expr, "Right side of 'in' must be a list literal"))
        return ExprType.BOOLEAN
    values = list(list_expr.elements)

    if isinstance(element, Ident):
        info = registry.get(element.name)
        if info is not None and info.kind == KindType.CATEGORY:
            for val_node in values:
                if isinstance(val_node, StringLit) and val_node.value not in info.category_values:
                    if info.category_extensible:
                        errors.append(
                            CelError(
                                expr,
                                f"Value '{val_node.value}' not in value set for category concept '{element.name}' (extensible, may be valid)",
                                is_warning=True,
                            )
                        )
                    else:
                        errors.append(
                            CelError(
                                expr,
                                f"Value '{val_node.value}' not in value set for category concept '{element.name}'",
                            )
                        )
        if info is not None and info.kind == KindType.BOOLEAN:
            errors.append(
                CelError(
                    expr,
                    f"Boolean concept '{element.name}' cannot be used with 'in' operator",
                )
            )
        if info is not None and info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            for val_node in values:
                if isinstance(val_node, StringLit):
                    errors.append(
                        CelError(
                            expr,
                            f"String literal in 'in' list for quantity concept '{element.name}'",
                        )
                    )

    return ExprType.BOOLEAN


def _check_ternary_call(
    node: Call,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> ExprType:
    condition, true_branch, false_branch = node.args
    condition_type = _resolve_type(condition, expr, registry, errors)
    if condition_type not in {ExprType.BOOLEAN, ExprType.UNKNOWN}:
        errors.append(
            CelError(
                expr,
                f"Ternary condition must be boolean, got {condition_type.value}",
            )
        )
    t1 = _resolve_type(true_branch, expr, registry, errors)
    t2 = _resolve_type(false_branch, expr, registry, errors)
    if t1 == ExprType.UNKNOWN or t2 == ExprType.UNKNOWN:
        return ExprType.UNKNOWN
    if t1 != t2:
        errors.append(
            CelError(
                expr,
                f"Ternary branches must have the same type, got {t1.value} and {t2.value}",
            )
        )
        return ExprType.UNKNOWN
    return t1


def _check_node(
    node: Expr,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> None:
    _resolve_type(node, expr, registry, errors)


def _check_disallowed_kind_usage(
    node: Expr,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
    *,
    operation_class: str,
) -> None:
    if isinstance(node, Ident):
        info = registry.get(node.name)
        message_template = (
            None
            if info is None
            else _DISALLOWED_KIND_USAGE.get(operation_class, {}).get(info.kind)
        )
        if message_template is not None:
            errors.append(CelError(expr, message_template.format(name=node.name)))


def _check_comparison_type_mismatch(
    left: Expr,
    right: Expr,
    left_type: ExprType,
    right_type: ExprType,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> None:
    if left_type in {ExprType.UNKNOWN} or right_type in {ExprType.UNKNOWN}:
        return
    if left_type == right_type:
        return
    if not isinstance(left, Ident) and not isinstance(right, Ident):
        return

    if _check_concept_literal_type_mismatch(
        left, right, right_type, expr, registry, errors
    ):
        return
    if _check_concept_literal_type_mismatch(
        right, left, left_type, expr, registry, errors
    ):
        return

    left_name = left.name if isinstance(left, Ident) else None
    right_name = right.name if isinstance(right, Ident) else None
    left_info = registry.get(left_name) if left_name is not None else None
    right_info = registry.get(right_name) if right_name is not None else None
    if left_info is not None and right_info is not None:
        errors.append(
            CelError(
                expr,
                "Cannot compare "
                f"{left_info.kind.value} concept '{left_name}' "
                f"to {right_info.kind.value} concept '{right_name}'",
            )
        )
        return

    errors.append(
        CelError(
            expr,
            f"Type mismatch: cannot compare {left_type.value} to {right_type.value}",
        )
    )


def _check_concept_literal_type_mismatch(
    concept_node: Expr,
    other_node: Expr,
    other_type: ExprType,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> bool:
    if not isinstance(concept_node, Ident):
        return False
    if not _is_literal(other_node):
        return False
    info = registry.get(concept_node.name)
    if info is None:
        return False

    if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT) and other_type == ExprType.STRING:
        errors.append(
            CelError(
                expr,
                f"Quantity concept '{concept_node.name}' compared to string literal",
            )
        )
        return True
    if info.kind == KindType.CATEGORY and other_type == ExprType.NUMERIC:
        errors.append(
            CelError(
                expr,
                f"Category concept '{concept_node.name}' compared to numeric literal",
            )
        )
        return True
    if info.kind == KindType.BOOLEAN and other_type == ExprType.STRING:
        errors.append(
            CelError(
                expr,
                f"Boolean concept '{concept_node.name}' compared to string literal",
            )
        )
        return True
    if info.kind == KindType.BOOLEAN and other_type == ExprType.NUMERIC:
        errors.append(
            CelError(
                expr,
                f"Boolean concept '{concept_node.name}' compared to numeric literal",
            )
        )
        return True
    return False


def _check_category_value(
    concept_node: Expr,
    value_node: Expr,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> None:
    if not isinstance(concept_node, Ident):
        return
    if not isinstance(value_node, StringLit):
        return
    info = registry.get(concept_node.name)
    if info is None or info.kind != KindType.CATEGORY:
        return

    if value_node.value not in info.category_values:
        if info.category_extensible:
            errors.append(
                CelError(
                    expr,
                    f"Value '{value_node.value}' not in value set for category concept '{concept_node.name}' (extensible, may be valid)",
                    is_warning=True,
                )
            )
        else:
            errors.append(
                CelError(
                    expr,
                    f"Value '{value_node.value}' not in value set for category concept '{concept_node.name}'",
                )
            )


def _is_literal(node: Expr) -> bool:
    return isinstance(node, (IntLit, UintLit, DoubleLit, StringLit, BytesLit, BoolLit, NullLit))


_SHORT_OPS: dict[str, str] = {
    OP_ADD: "+",
    OP_SUB: "-",
    OP_MUL: "*",
    OP_DIV: "/",
    OP_MOD: "%",
    OP_EQ: "==",
    OP_NE: "!=",
    OP_LT: "<",
    OP_LE: "<=",
    OP_GT: ">",
    OP_GE: ">=",
    OP_AND: "&&",
    OP_OR: "||",
}


def _short_op(function: str) -> str:
    return _SHORT_OPS.get(function, function)


def condition_ir_from_cel(
    source: str,
    registry: Mapping[str, ConceptInfo],
) -> ConditionIR:
    errors = check_cel_expression(source, registry)
    hard_errors = [error for error in errors if not error.is_warning]
    if hard_errors:
        message = "; ".join(error.message for error in hard_errors)
        raise ValueError(message)
    try:
        ast = parse(source)
    except ParseError as exc:
        raise ValueError(f"Parse error: {exc}") from exc
    return _lower_node(ast, registry)


def check_condition_ir(
    source: str,
    registry: Mapping[str, ConceptInfo],
) -> CheckedCondition:
    errors = check_cel_expression(source, registry)
    hard_errors = [error for error in errors if not error.is_warning]
    if hard_errors:
        message = "; ".join(error.message for error in hard_errors)
        raise ValueError(message)
    try:
        ast = parse(source)
    except ParseError as exc:
        raise ValueError(f"Parse error: {exc}") from exc
    return CheckedCondition(
        source=source,
        ir=_lower_node(ast, registry),
        registry_fingerprint=str(condition_registry_fingerprint(registry)),
        warnings=tuple(error.message for error in errors if error.is_warning),
    )


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

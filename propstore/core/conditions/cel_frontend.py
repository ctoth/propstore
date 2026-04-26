"""CEL frontend adapter that lowers checked CEL source into ConditionIR."""

from __future__ import annotations

from collections.abc import Mapping

from propstore.cel_checker import (
    ASTNode,
    BinaryOpNode,
    CheckedCelExpr,
    ConceptInfo,
    InNode,
    KindType,
    LiteralNode,
    NameNode,
    TernaryNode,
    UnaryOpNode,
    check_cel_expr,
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
    span = ConditionSourceSpan(0, len(str(checked.source)))
    return _lower_node(checked.ast, registry, span)


def _lower_node(
    node: ASTNode,
    registry: Mapping[str, ConceptInfo],
    span: ConditionSourceSpan,
) -> ConditionIR:
    if isinstance(node, NameNode):
        return _lower_name(node, registry, span)
    if isinstance(node, LiteralNode):
        return _lower_literal(node, span)
    if isinstance(node, UnaryOpNode):
        return ConditionUnary(
            op=ConditionUnaryOp(node.op),
            operand=_lower_node(node.operand, registry, span),
            span=span,
        )
    if isinstance(node, BinaryOpNode):
        return ConditionBinary(
            op=ConditionBinaryOp(node.op),
            left=_lower_node(node.left, registry, span),
            right=_lower_node(node.right, registry, span),
            span=span,
        )
    if isinstance(node, InNode):
        return ConditionMembership(
            element=_lower_node(node.expr, registry, span),
            options=tuple(_lower_node(value, registry, span) for value in node.values),
            span=span,
        )
    if isinstance(node, TernaryNode):
        return ConditionChoice(
            condition=_lower_node(node.condition, registry, span),
            when_true=_lower_node(node.true_branch, registry, span),
            when_false=_lower_node(node.false_branch, registry, span),
            span=span,
        )
    raise TypeError(f"unsupported CEL AST node: {type(node).__name__}")


def _lower_name(
    node: NameNode,
    registry: Mapping[str, ConceptInfo],
    span: ConditionSourceSpan,
) -> ConditionReference:
    info = registry.get(node.name)
    if info is None:
        raise ValueError(f"Undefined concept: {node.name}")
    if info.kind == KindType.STRUCTURAL:
        raise ValueError(f"Structural concept '{node.name}' cannot appear in ConditionIR")
    return ConditionReference(
        concept_id=info.id,
        source_name=node.name,
        value_kind=_value_kind(info.kind),
        span=span,
    )


def _lower_literal(
    node: LiteralNode,
    span: ConditionSourceSpan,
) -> ConditionLiteral:
    if node.lit_type == "bool" and isinstance(node.value, bool):
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.BOOLEAN,
            span=span,
        )
    if node.lit_type in {"int", "float"} and isinstance(node.value, int | float):
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.NUMERIC,
            span=span,
        )
    if node.lit_type == "string" and isinstance(node.value, str):
        return ConditionLiteral(
            value=node.value,
            value_kind=ConditionValueKind.STRING,
            span=span,
        )
    raise TypeError(f"unsupported CEL literal: {node.lit_type}")


def _value_kind(kind: KindType) -> ConditionValueKind:
    if kind in (KindType.QUANTITY, KindType.TIMEPOINT):
        return ConditionValueKind.NUMERIC
    if kind == KindType.CATEGORY:
        return ConditionValueKind.STRING
    if kind == KindType.BOOLEAN:
        return ConditionValueKind.BOOLEAN
    raise ValueError(f"Structural concept kind cannot lower to ConditionIR: {kind.value}")

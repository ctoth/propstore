from __future__ import annotations

from quire.charter_class import CharterDoc

from propstore.core.conditions.checked import CheckedCondition, CheckedConditionSet
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
from propstore.core.id_types import ConceptId


class ConditionSourceSpanDocument(CharterDoc):
    start: int
    end: int


class ConditionLiteralDocument(
    CharterDoc, tag="literal", tag_field="node", kw_only=True
):
    value: bool | int | float | str
    value_kind: str
    span: ConditionSourceSpanDocument


class ConditionReferenceDocument(
    CharterDoc, tag="reference", tag_field="node", kw_only=True
):
    concept_id: str
    source_name: str
    value_kind: str
    span: ConditionSourceSpanDocument
    category_values: tuple[str, ...] = ()
    category_extensible: bool | None = None


class ConditionUnaryDocument(CharterDoc, tag="unary", tag_field="node", kw_only=True):
    op: str
    operand: "ConditionIRDocument"
    span: ConditionSourceSpanDocument


class ConditionBinaryDocument(CharterDoc, tag="binary", tag_field="node", kw_only=True):
    op: str
    left: "ConditionIRDocument"
    right: "ConditionIRDocument"
    span: ConditionSourceSpanDocument


class ConditionMembershipDocument(
    CharterDoc, tag="membership", tag_field="node", kw_only=True
):
    element: "ConditionIRDocument"
    options: tuple["ConditionIRDocument", ...]
    span: ConditionSourceSpanDocument


class ConditionChoiceDocument(CharterDoc, tag="choice", tag_field="node", kw_only=True):
    condition: "ConditionIRDocument"
    when_true: "ConditionIRDocument"
    when_false: "ConditionIRDocument"
    span: ConditionSourceSpanDocument


ConditionIRDocument = (
    ConditionLiteralDocument
    | ConditionReferenceDocument
    | ConditionUnaryDocument
    | ConditionBinaryDocument
    | ConditionMembershipDocument
    | ConditionChoiceDocument
)


class CheckedConditionDocument(CharterDoc):
    source: str
    ir: ConditionIRDocument
    registry_fingerprint: str
    warnings: tuple[str, ...] = ()


class CheckedConditionSetDocument(CharterDoc):
    registry_fingerprint: str
    conditions: tuple[CheckedConditionDocument, ...] = ()


def condition_ir_document(condition: ConditionIR) -> ConditionIRDocument:
    if isinstance(condition, ConditionLiteral):
        return ConditionLiteralDocument(
            value=condition.value,
            value_kind=condition.value_kind.value,
            span=_span_document(condition.span),
        )
    if isinstance(condition, ConditionReference):
        return ConditionReferenceDocument(
            concept_id=str(condition.concept_id),
            source_name=condition.source_name,
            value_kind=condition.value_kind.value,
            span=_span_document(condition.span),
            category_values=condition.category_values,
            category_extensible=condition.category_extensible,
        )
    if isinstance(condition, ConditionUnary):
        return ConditionUnaryDocument(
            op=condition.op.value,
            operand=condition_ir_document(condition.operand),
            span=_span_document(condition.span),
        )
    if isinstance(condition, ConditionBinary):
        return ConditionBinaryDocument(
            op=condition.op.value,
            left=condition_ir_document(condition.left),
            right=condition_ir_document(condition.right),
            span=_span_document(condition.span),
        )
    if isinstance(condition, ConditionMembership):
        return ConditionMembershipDocument(
            element=condition_ir_document(condition.element),
            options=tuple(
                condition_ir_document(option) for option in condition.options
            ),
            span=_span_document(condition.span),
        )
    if isinstance(condition, ConditionChoice):
        return ConditionChoiceDocument(
            condition=condition_ir_document(condition.condition),
            when_true=condition_ir_document(condition.when_true),
            when_false=condition_ir_document(condition.when_false),
            span=_span_document(condition.span),
        )
    raise TypeError(f"unsupported ConditionIR node: {type(condition).__name__}")


def condition_ir_semantic(document: ConditionIRDocument) -> ConditionIR:
    if isinstance(document, ConditionLiteralDocument):
        return ConditionLiteral(
            value=document.value,
            value_kind=ConditionValueKind(document.value_kind),
            span=_span_semantic(document.span),
        )
    if isinstance(document, ConditionReferenceDocument):
        return ConditionReference(
            concept_id=ConceptId(document.concept_id),
            source_name=document.source_name,
            value_kind=ConditionValueKind(document.value_kind),
            span=_span_semantic(document.span),
            category_values=document.category_values,
            category_extensible=document.category_extensible,
        )
    if isinstance(document, ConditionUnaryDocument):
        return ConditionUnary(
            op=ConditionUnaryOp(document.op),
            operand=condition_ir_semantic(document.operand),
            span=_span_semantic(document.span),
        )
    if isinstance(document, ConditionBinaryDocument):
        return ConditionBinary(
            op=ConditionBinaryOp(document.op),
            left=condition_ir_semantic(document.left),
            right=condition_ir_semantic(document.right),
            span=_span_semantic(document.span),
        )
    if isinstance(document, ConditionMembershipDocument):
        return ConditionMembership(
            element=condition_ir_semantic(document.element),
            options=tuple(condition_ir_semantic(option) for option in document.options),
            span=_span_semantic(document.span),
        )
    if isinstance(document, ConditionChoiceDocument):
        return ConditionChoice(
            condition=condition_ir_semantic(document.condition),
            when_true=condition_ir_semantic(document.when_true),
            when_false=condition_ir_semantic(document.when_false),
            span=_span_semantic(document.span),
        )
    raise TypeError(f"unsupported ConditionIR document: {type(document).__name__}")


def checked_condition_document(condition: CheckedCondition) -> CheckedConditionDocument:
    return CheckedConditionDocument(
        source=condition.source,
        ir=condition_ir_document(condition.ir),
        registry_fingerprint=condition.registry_fingerprint,
        warnings=condition.warnings,
    )


def checked_condition_semantic(document: CheckedConditionDocument) -> CheckedCondition:
    return CheckedCondition(
        source=document.source,
        ir=condition_ir_semantic(document.ir),
        registry_fingerprint=document.registry_fingerprint,
        warnings=document.warnings,
    )


def checked_condition_set_document(
    condition_set: CheckedConditionSet | None,
) -> CheckedConditionSetDocument | None:
    if condition_set is None:
        return None
    return CheckedConditionSetDocument(
        registry_fingerprint=condition_set.registry_fingerprint,
        conditions=tuple(
            checked_condition_document(condition)
            for condition in condition_set.conditions
        ),
    )


def checked_condition_set_semantic(
    document: CheckedConditionSetDocument | None,
) -> CheckedConditionSet | None:
    if document is None:
        return None
    return CheckedConditionSet(
        conditions=tuple(
            checked_condition_semantic(condition) for condition in document.conditions
        ),
        registry_fingerprint=document.registry_fingerprint,
    )


def _span_document(span: ConditionSourceSpan) -> ConditionSourceSpanDocument:
    return ConditionSourceSpanDocument(start=span.start, end=span.end)


def _span_semantic(document: ConditionSourceSpanDocument) -> ConditionSourceSpan:
    return ConditionSourceSpan(document.start, document.end)

"""Typed source boundary for structural situated assertions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
    RoleSignature,
)


@dataclass(frozen=True)
class AssertionSourceRecord:
    """Boundary-normalized structural assertion source record.

    The decoded source mapping is accepted only at this boundary. Everything
    beyond it receives closed assertion and relation domain objects.
    """

    relation: RelationConceptRef
    role_bindings: RoleBindingSet
    context: ContextReference
    condition: ConditionRef
    provenance_ref: ProvenanceGraphRef

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> AssertionSourceRecord:
        return assertion_source_record_from_payload(payload)

    def to_situated_assertion(
        self,
        *,
        signature: RoleSignature | None = None,
    ) -> SituatedAssertion:
        if signature is not None:
            signature.validate_bindings(self.role_bindings)
        return SituatedAssertion(
            relation=self.relation,
            role_bindings=self.role_bindings,
            context=self.context,
            condition=self.condition,
            provenance_ref=self.provenance_ref,
        )


def assertion_source_record_from_payload(
    payload: Mapping[str, object],
) -> AssertionSourceRecord:
    if _has_old_claim_shape(payload):
        raise ValueError("structural assertion payload is required")

    return AssertionSourceRecord(
        relation=_relation_ref(_required(payload, "relation")),
        role_bindings=_role_binding_set(_required(payload, "roles")),
        context=_context_ref(_required(payload, "context")),
        condition=_condition_ref(_required(payload, "condition_ref")),
        provenance_ref=_graph_ref(_required(payload, "provenance_ref")),
    )


def _required(payload: Mapping[str, object], key: str) -> object:
    if key not in payload:
        raise ValueError(f"missing structural assertion field: {key}")
    return payload[key]


def _has_old_claim_shape(payload: Mapping[str, object]) -> bool:
    old_keys = {"type", "statement", "concepts", "concept"}
    return bool(old_keys.intersection(payload.keys()))


def _relation_ref(value: object) -> RelationConceptRef:
    if not isinstance(value, Mapping):
        raise TypeError("relation must be a mapping")
    concept_value = _required(value, "concept_id")
    lexical_value = value.get("lexical_sense_id")
    description_value = value.get("description_kind_id")
    return RelationConceptRef(
        concept_id=_text(concept_value, "relation concept id"),
        lexical_sense_id=None
        if lexical_value is None
        else _text(lexical_value, "lexical sense id"),
        description_kind_id=None
        if description_value is None
        else _text(description_value, "description kind id"),
    )


def _role_binding_set(value: object) -> RoleBindingSet:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError("roles must be a sequence")
    return RoleBindingSet(tuple(_role_binding(item) for item in value))


def _role_binding(value: object) -> RoleBinding:
    if not isinstance(value, Mapping):
        raise TypeError("role binding must be a mapping")
    return RoleBinding(
        role=_text(_required(value, "role"), "role"),
        value=_text(_required(value, "value"), "role value"),
    )


def _context_ref(value: object) -> ContextReference:
    return ContextReference(_text(value, "context"))


def _condition_ref(value: object) -> ConditionRef:
    if not isinstance(value, Mapping):
        raise TypeError("condition reference must be a mapping")
    return ConditionRef(
        id=_text(_required(value, "id"), "condition id"),
        registry_fingerprint=_text(
            _required(value, "registry_fingerprint"),
            "registry fingerprint",
        ),
    )


def _graph_ref(value: object) -> ProvenanceGraphRef:
    return ProvenanceGraphRef(_text(value, "provenance graph reference"))


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value

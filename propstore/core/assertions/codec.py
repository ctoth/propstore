"""Canonical serialization boundary for situated assertions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import AssertionId
from propstore.core.id_types import ConditionId, ContextId, ProvenanceGraphId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet


@dataclass(frozen=True)
class AssertionCanonicalRecord:
    """Canonical serialized form of one situated assertion.

    The record is the closed object used inside the core. The mapping returned
    by ``to_payload`` is only for serialization and external IO boundaries.
    """

    assertion_id: AssertionId | str
    relation: RelationConceptRef
    role_bindings: RoleBindingSet
    context: ContextReference
    condition: ConditionRef
    provenance_ref: ProvenanceGraphRef

    def __post_init__(self) -> None:
        assertion_id = AssertionId(self.assertion_id)
        expected_id = self.to_assertion().assertion_id
        if assertion_id != expected_id:
            raise ValueError("assertion id does not match canonical assertion")
        object.__setattr__(self, "assertion_id", assertion_id)

    @classmethod
    def from_assertion(cls, assertion: SituatedAssertion) -> AssertionCanonicalRecord:
        return cls(
            assertion_id=assertion.assertion_id,
            relation=assertion.relation,
            role_bindings=assertion.role_bindings,
            context=assertion.context,
            condition=assertion.condition,
            provenance_ref=assertion.provenance_ref,
        )

    def to_assertion(self) -> SituatedAssertion:
        return SituatedAssertion(
            relation=self.relation,
            role_bindings=self.role_bindings,
            context=self.context,
            condition=self.condition,
            provenance_ref=self.provenance_ref,
        )


def _relation_ref(value: object) -> RelationConceptRef:
    if not isinstance(value, Mapping):
        raise TypeError("relation must be a mapping")
    return RelationConceptRef(
        concept_id=_text(_required(value, "concept_id"), "relation concept id")
    )


def _role_binding_set(value: object) -> RoleBindingSet:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError("role bindings must be a sequence")
    return RoleBindingSet(tuple(_role_binding(item) for item in value))


def _role_binding(value: object) -> RoleBinding:
    if not isinstance(value, Mapping):
        raise TypeError("role binding must be a mapping")
    return RoleBinding(
        role=_text(_required(value, "role"), "role"),
        value=_text(_required(value, "value"), "role value"),
    )


def _context_ref(value: object) -> ContextReference:
    if not isinstance(value, Mapping):
        raise TypeError("context must be a mapping")
    return ContextReference(ContextId(_text(_required(value, "id"), "context id")))


def _condition_ref(value: object) -> ConditionRef:
    if not isinstance(value, Mapping):
        raise TypeError("condition reference must be a mapping")
    return ConditionRef(
        id=ConditionId(_text(_required(value, "id"), "condition id")),
        registry_fingerprint=_text(
            _required(value, "registry_fingerprint"),
            "registry fingerprint",
        ),
    )


def _graph_ref(value: object) -> ProvenanceGraphRef:
    if not isinstance(value, Mapping):
        raise TypeError("provenance graph reference must be a mapping")
    return ProvenanceGraphRef(
        ProvenanceGraphId(
            _text(_required(value, "graph_name"), "provenance graph name")
        )
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value

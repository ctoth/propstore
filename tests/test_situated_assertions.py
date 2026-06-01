from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.assertions.refs import (
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.assertions.situated import SituatedAssertion
from propstore.core.id_types import ConceptId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet


def test_situated_assertion_identity_includes_structural_parts() -> None:
    base = _published_in_assertion()
    different_context = _published_in_assertion(context=ContextReference("ctx_other"))
    different_condition = _published_in_assertion(
        condition=ConditionRef(
            id="ps:condition:peer-reviewed",
            registry_fingerprint="registry:sha256:concept-registry",
        )
    )

    assert base.assertion_id != different_context.assertion_id
    assert base.assertion_id != different_condition.assertion_id


def test_rival_normalized_candidates_can_coexist_with_distinct_identities() -> None:
    subtype = RelationConceptRef(ConceptId("ps:concept:relation:subtype_of"))
    instance = RelationConceptRef(ConceptId("ps:concept:relation:instance_of"))
    shared_context = ContextReference("ctx_source")
    shared_condition = ConditionRef.unconditional()
    shared_provenance = ProvenanceGraphRef("urn:propstore:provenance:source")

    subtype_candidate = SituatedAssertion(
        relation=subtype,
        role_bindings=RoleBindingSet(
            (
                RoleBinding("subtype", "ps:concept:method:rct"),
                RoleBinding("supertype", "ps:concept:method:empirical"),
            )
        ),
        context=shared_context,
        condition=shared_condition,
        provenance_ref=shared_provenance,
    )
    instance_candidate = SituatedAssertion(
        relation=instance,
        role_bindings=RoleBindingSet(
            (
                RoleBinding("instance", "ps:concept:method:rct"),
                RoleBinding("type", "ps:concept:method:empirical"),
            )
        ),
        context=shared_context,
        condition=shared_condition,
        provenance_ref=shared_provenance,
    )

    assert subtype_candidate.assertion_id != instance_candidate.assertion_id


def _published_in_assertion(
    *,
    role_bindings: RoleBindingSet | None = None,
    context: ContextReference | None = None,
    condition: ConditionRef | None = None,
    provenance: ProvenanceGraphRef | None = None,
) -> SituatedAssertion:
    return SituatedAssertion(
        relation=RelationConceptRef(ConceptId("ps:concept:relation:published_in")),
        role_bindings=role_bindings
        or RoleBindingSet(
            (
                RoleBinding("paper", "ps:concept:paper:clark-2014"),
                RoleBinding("venue", "ps:concept:venue:j-biomed-semantics"),
            )
        ),
        context=context or ContextReference("ctx_literature"),
        condition=condition or ConditionRef.unconditional(),
        provenance_ref=provenance
        or ProvenanceGraphRef("urn:propstore:provenance:default"),
    )

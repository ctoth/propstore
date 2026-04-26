from __future__ import annotations

import pytest

from propstore.core.assertions import (
    AssertionSourceRecord,
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
    SituatedAssertion,
)
from propstore.core.id_types import ConceptId
from propstore.core.relations import (
    RelationConceptRef,
    RoleBinding,
    RoleBindingSet,
    RoleDefinition,
    RoleSignature,
)


def test_payload_converts_to_typed_source_record_at_boundary() -> None:
    record = AssertionSourceRecord.from_payload(_published_in_payload())

    assert record.relation == RelationConceptRef(
        ConceptId("ps:concept:relation:published_in")
    )
    assert record.role_bindings == RoleBindingSet((
        RoleBinding("paper", "ps:concept:paper:clark-2014"),
        RoleBinding("venue", "ps:concept:venue:j-biomed-semantics"),
    ))
    assert record.context == ContextReference("ctx_literature")
    assert record.condition == ConditionRef.unconditional()
    assert record.provenance_ref == ProvenanceGraphRef(
        "urn:propstore:provenance:source"
    )


def test_source_record_converts_to_situated_assertion() -> None:
    record = AssertionSourceRecord.from_payload(_published_in_payload())
    assertion = record.to_situated_assertion()

    assert assertion == SituatedAssertion(
        relation=RelationConceptRef(ConceptId("ps:concept:relation:published_in")),
        role_bindings=RoleBindingSet((
            RoleBinding("paper", "ps:concept:paper:clark-2014"),
            RoleBinding("venue", "ps:concept:venue:j-biomed-semantics"),
        )),
        context=ContextReference("ctx_literature"),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef("urn:propstore:provenance:source"),
    )
    assert str(assertion.assertion_id).startswith("ps:assertion:")


def test_source_record_validates_role_signature_during_conversion() -> None:
    record = AssertionSourceRecord.from_payload(_published_in_payload())
    assertion = record.to_situated_assertion(signature=_published_in_signature())

    assert assertion.role_bindings.identity_payload() == (
        ("paper", "ps:concept:paper:clark-2014"),
        ("venue", "ps:concept:venue:j-biomed-semantics"),
    )


def test_source_record_rejects_unknown_role_during_conversion() -> None:
    payload = _published_in_payload()
    payload["roles"] = [
        {"role": "paper", "value": "ps:concept:paper:clark-2014"},
        {"role": "publisher", "value": "ps:concept:publisher:w3c"},
        {"role": "venue", "value": "ps:concept:venue:j-biomed-semantics"},
    ]
    record = AssertionSourceRecord.from_payload(payload)

    with pytest.raises(ValueError, match="unknown role"):
        record.to_situated_assertion(signature=_published_in_signature())


def test_source_record_rejects_old_claim_shaped_payloads() -> None:
    payload = {
        "type": "observation",
        "statement": "Clark 2014 was published in the Journal of Biomedical Semantics.",
        "concepts": ["ps:concept:paper:clark-2014"],
    }

    with pytest.raises(ValueError, match="structural assertion"):
        AssertionSourceRecord.from_payload(payload)


def _published_in_payload() -> dict[str, object]:
    return {
        "relation": {"concept_id": "ps:concept:relation:published_in"},
        "roles": [
            {"role": "venue", "value": "ps:concept:venue:j-biomed-semantics"},
            {"role": "paper", "value": "ps:concept:paper:clark-2014"},
        ],
        "context": "ctx_literature",
        "condition_ref": {
            "id": "ps:condition:unconditional",
            "registry_fingerprint": "registry:unconditional",
        },
        "provenance_ref": "urn:propstore:provenance:source",
    }


def _published_in_signature() -> RoleSignature:
    relation = RelationConceptRef(ConceptId("ps:concept:relation:published_in"))
    return RoleSignature(
        relation=relation,
        role_definitions=(
            RoleDefinition(
                role="paper",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:paper"),
            ),
            RoleDefinition(
                role="venue",
                domain=ConceptId("ps:concept:class:publication_event"),
                range=ConceptId("ps:concept:class:venue"),
            ),
        ),
    )

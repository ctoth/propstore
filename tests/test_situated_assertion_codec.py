from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.assertions import (
    AssertionCanonicalRecord,
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
    SituatedAssertion,
)
from propstore.core.id_types import ConceptId
from propstore.core.relations import RelationConceptRef, RoleBinding, RoleBindingSet


def test_canonical_record_renders_situated_assertion_payload() -> None:
    assertion = _published_in_assertion()
    record = AssertionCanonicalRecord.from_assertion(assertion)

    assert record.assertion_id == assertion.assertion_id
    assert record.to_payload() == {
        "assertion_id": str(assertion.assertion_id),
        "relation": {"concept_id": "ps:concept:relation:published_in"},
        "role_bindings": [
            {"role": "paper", "value": "ps:concept:paper:clark-2014"},
            {"role": "venue", "value": "ps:concept:venue:j-biomed-semantics"},
        ],
        "context": {"id": "ctx_literature"},
        "condition_ref": {
            "id": "ps:condition:unconditional",
            "registry_fingerprint": "registry:unconditional",
        },
        "provenance_ref": {"graph_name": "urn:propstore:provenance:source"},
    }


def test_canonical_payload_parses_back_to_same_situated_assertion() -> None:
    assertion = _published_in_assertion()
    payload = AssertionCanonicalRecord.from_assertion(assertion).to_payload()

    parsed = AssertionCanonicalRecord.from_payload(payload).to_assertion()

    assert parsed == assertion
    assert parsed.assertion_id == assertion.assertion_id


@given(st.permutations((
    {"role": "paper", "value": "ps:concept:paper:clark-2014"},
    {"role": "venue", "value": "ps:concept:venue:j-biomed-semantics"},
)))
def test_canonical_payload_parse_canonicalizes_role_order(
    role_bindings: tuple[dict[str, str], ...],
) -> None:
    assertion = _published_in_assertion()
    payload = AssertionCanonicalRecord.from_assertion(assertion).to_payload()
    payload["role_bindings"] = list(role_bindings)

    parsed = AssertionCanonicalRecord.from_payload(payload)

    assert parsed.role_bindings.identity_payload() == (
        ("paper", "ps:concept:paper:clark-2014"),
        ("venue", "ps:concept:venue:j-biomed-semantics"),
    )


def test_canonical_payload_rejects_old_claim_shaped_fields() -> None:
    payload = {
        "claim_id": "claim:old",
        "predicate_id": "published_in",
        "arguments": ["ps:concept:paper:clark-2014"],
    }

    with pytest.raises(ValueError, match="canonical situated assertion"):
        AssertionCanonicalRecord.from_payload(payload)


def test_canonical_payload_rejects_mismatched_assertion_id() -> None:
    assertion = _published_in_assertion()
    payload = AssertionCanonicalRecord.from_assertion(assertion).to_payload()
    payload["assertion_id"] = "ps:assertion:ffffffffffffffffffffffffffffffff"

    with pytest.raises(ValueError, match="assertion id"):
        AssertionCanonicalRecord.from_payload(payload)


def _published_in_assertion() -> SituatedAssertion:
    return SituatedAssertion(
        relation=RelationConceptRef(ConceptId("ps:concept:relation:published_in")),
        role_bindings=RoleBindingSet((
            RoleBinding("paper", "ps:concept:paper:clark-2014"),
            RoleBinding("venue", "ps:concept:venue:j-biomed-semantics"),
        )),
        context=ContextReference("ctx_literature"),
        condition=ConditionRef.unconditional(),
        provenance_ref=ProvenanceGraphRef("urn:propstore:provenance:source"),
    )

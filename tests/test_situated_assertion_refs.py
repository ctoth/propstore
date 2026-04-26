from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.assertions import (
    UNCONDITIONAL_CONDITION_REF,
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.id_types import ConditionId, ContextId, ProvenanceGraphId


def test_context_reference_is_owned_by_assertion_core() -> None:
    context = ContextReference(ContextId("ctx_lab"))

    assert not isinstance(context, str)
    assert context.identity_payload() == ("context", "ctx_lab")


def test_context_reference_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="context id"):
        ContextReference("")


def test_condition_ref_is_closed_identity_reference_not_raw_cel() -> None:
    condition = ConditionRef(
        id=ConditionId("ps:condition:84e9d2"),
        registry_fingerprint="registry:sha256:concept-registry",
    )

    assert not isinstance(condition, str)
    assert condition.identity_payload() == (
        "condition",
        "ps:condition:84e9d2",
        "registry:sha256:concept-registry",
    )


def test_condition_ref_has_unconditional_sentinel() -> None:
    assert UNCONDITIONAL_CONDITION_REF == ConditionRef.unconditional()
    assert UNCONDITIONAL_CONDITION_REF.identity_payload() == (
        "condition",
        "ps:condition:unconditional",
        "registry:unconditional",
    )


def test_condition_ref_rejects_raw_looking_cel_and_missing_fingerprint() -> None:
    with pytest.raises(ValueError, match="condition id"):
        ConditionRef(
            id="room_type == 'lab'",
            registry_fingerprint="registry:sha256:concept-registry",
        )

    with pytest.raises(ValueError, match="registry fingerprint"):
        ConditionRef(id=ConditionId("ps:condition:84e9d2"), registry_fingerprint="")


def test_provenance_graph_ref_is_named_graph_reference_not_payload() -> None:
    graph = ProvenanceGraphRef(ProvenanceGraphId("ni:///sha-256;abc123"))

    assert not isinstance(graph, str)
    assert graph.identity_payload() == (
        "provenance_graph",
        "ni:///sha-256;abc123",
    )


def test_provenance_graph_ref_rejects_empty_non_uri_and_payload_values() -> None:
    with pytest.raises(ValueError, match="provenance graph"):
        ProvenanceGraphRef("")
    with pytest.raises(ValueError, match="provenance graph"):
        ProvenanceGraphRef("claim:left")
    with pytest.raises(TypeError, match="provenance graph"):
        ProvenanceGraphRef({"status": "stated"})


@given(
    st.permutations((
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:a")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:b")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:c")),
    )),
)
def test_provenance_graph_refs_sort_by_named_graph_identity(
    refs: tuple[ProvenanceGraphRef, ...],
) -> None:
    assert tuple(sorted(refs)) == (
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:a")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:b")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:c")),
    )

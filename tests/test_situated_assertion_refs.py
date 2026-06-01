from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.core.assertions.refs import (
    UNCONDITIONAL_CONDITION_REF,
    ConditionRef,
    ContextReference,
    ProvenanceGraphRef,
)
from propstore.core.id_types import (
    ConditionId,
    ContextId,
    ProvenanceGraphId,
)


def test_context_reference_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="context id"):
        ContextReference("")


def test_condition_ref_rejects_raw_looking_cel_and_missing_fingerprint() -> None:
    with pytest.raises(ValueError, match="condition id"):
        ConditionRef(
            id="room_type == 'lab'",
            registry_fingerprint="registry:sha256:concept-registry",
        )

    with pytest.raises(ValueError, match="registry fingerprint"):
        ConditionRef(id=ConditionId("ps:condition:84e9d2"), registry_fingerprint="")


@pytest.mark.property
@given(
    st.permutations(
        (
            ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:a")),
            ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:b")),
            ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:c")),
        )
    ),
)
def test_provenance_graph_refs_sort_by_named_graph_identity(
    refs: tuple[ProvenanceGraphRef, ...],
) -> None:
    assert tuple(sorted(refs)) == (
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:a")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:b")),
        ProvenanceGraphRef(ProvenanceGraphId("urn:propstore:provenance:c")),
    )

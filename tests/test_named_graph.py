"""Named-graph provenance carrier (Carroll 2005) + git-note physical carrier.

Translated from the reference ``test_provenance_foundations`` carrier cases. The
opinion-fusion and family-document cases of that reference test belong to the
opinion / families-document slices (``propstore.opinion`` and
``propstore.families.*.documents`` are not part of the provenance carrier) and
are ported with those slices.
"""

from __future__ import annotations

import json

import pytest
from dulwich.objects import Blob
from dulwich.repo import MemoryRepo
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.provenance import (
    PROVENANCE_NOTES_REF,
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    compose_provenance,
    decode_named_graph,
    encode_named_graph,
    read_provenance_note,
    write_provenance_note,
)


def _witness(label: str) -> ProvenanceWitness:
    return ProvenanceWitness(
        asserter=f"agent:{label}",
        timestamp="2026-04-17T00:00:00Z",
        source_artifact_code=f"claim:{label}",
        method="stated",
    )


def _provenance(status: ProvenanceStatus, label: str) -> Provenance:
    return Provenance(status=status, witnesses=(_witness(label),))


@st.composite
def provenance_records(draw: st.DrawFn) -> Provenance:
    status = draw(st.sampled_from(tuple(ProvenanceStatus)))
    label = draw(st.text(min_size=1, max_size=8))
    return _provenance(status, label)


def test_named_graph_round_trips_byte_identically() -> None:
    provenance = Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(_witness("source-a"),),
        graph_name="ni:///sha-256/example",
    )

    encoded = encode_named_graph(provenance)
    decoded = decode_named_graph(encoded)

    assert decoded == provenance
    assert encode_named_graph(decoded) == encoded
    assert b"NamedGraph" in encoded


def test_named_graph_encoding_requires_explicit_uri_graph_name() -> None:
    # Carroll 2005 page images 001 and 004 make graph naming explicit: a
    # provenance carrier is a named graph, not an anonymous provenance blob.
    with pytest.raises(ValueError, match="graph_name"):
        encode_named_graph(_provenance(ProvenanceStatus.STATED, "source-a"))

    with pytest.raises(ValueError, match="URI"):
        encode_named_graph(
            Provenance(
                status=ProvenanceStatus.STATED,
                witnesses=(_witness("source-a"),),
                graph_name="claim:source-a",
            )
        )


def test_named_graph_payload_canonicalizes_sets_but_preserves_operation_order() -> None:
    # Witnesses and derived graph names are sets for identity purposes. Operations
    # are a causal trace, so their first-observed order is semantically meaningful.
    first = Provenance(
        status=ProvenanceStatus.CALIBRATED,
        witnesses=(_witness("b"), _witness("a"), _witness("b")),
        graph_name="urn:propstore:provenance:canonical",
        derived_from=("urn:graph:z", "urn:graph:a", "urn:graph:z"),
        operations=("projection", "import", "projection"),
    )
    second = Provenance(
        status=ProvenanceStatus.CALIBRATED,
        witnesses=(_witness("a"), _witness("b")),
        graph_name="urn:propstore:provenance:canonical",
        derived_from=("urn:graph:a", "urn:graph:z"),
        operations=("import", "projection"),
    )

    encoded = encode_named_graph(first)
    second_encoded = encode_named_graph(second)

    assert encoded != second_encoded
    assert decode_named_graph(encoded) == Provenance(
        status=ProvenanceStatus.CALIBRATED,
        witnesses=(_witness("a"), _witness("b")),
        graph_name="urn:propstore:provenance:canonical",
        derived_from=("urn:graph:a", "urn:graph:z"),
        operations=("projection", "import"),
    )
    assert decode_named_graph(second_encoded) == second

    payload = json.loads(encoded)
    assert payload["@id"] == "urn:propstore:provenance:canonical"
    assert payload["provenance"]["witnesses"] == [
        {
            "asserter": "agent:a",
            "method": "stated",
            "source_artifact_code": "claim:a",
            "timestamp": "2026-04-17T00:00:00Z",
        },
        {
            "asserter": "agent:b",
            "method": "stated",
            "source_artifact_code": "claim:b",
            "timestamp": "2026-04-17T00:00:00Z",
        },
    ]
    assert payload["provenance"]["derived_from"] == ["urn:graph:a", "urn:graph:z"]
    assert payload["provenance"]["operations"] == ["projection", "import"]


def test_git_notes_round_trip_named_graph_content() -> None:
    repo = MemoryRepo()
    claim_blob = Blob.from_string(b"claim payload")
    repo.object_store.add_object(claim_blob)
    provenance = Provenance(
        status=ProvenanceStatus.MEASURED,
        witnesses=(_witness("claim"),),
        graph_name="urn:propstore:provenance:claim",
    )
    encoded = encode_named_graph(provenance)

    note_commit = write_provenance_note(repo, claim_blob.id, provenance)

    assert note_commit is not None
    assert repo.refs[PROVENANCE_NOTES_REF] == note_commit
    assert read_provenance_note(repo, claim_blob.id) == provenance
    stored = read_provenance_note(repo, claim_blob.id)
    assert stored is not None
    assert encode_named_graph(stored) == encoded


def test_provenance_note_does_not_touch_annotated_object() -> None:
    # The physical carrier is a git note; the annotated blob must be byte-for-byte
    # unchanged so provenance never contaminates content identity (CLAUDE.md).
    repo = MemoryRepo()
    claim_blob = Blob.from_string(b"claim payload")
    repo.object_store.add_object(claim_blob)
    original_sha = claim_blob.id

    write_provenance_note(
        repo,
        claim_blob.id,
        Provenance(
            status=ProvenanceStatus.MEASURED,
            witnesses=(_witness("claim"),),
            graph_name="urn:propstore:provenance:claim",
        ),
    )

    reread = repo.get_object(original_sha)
    assert reread.id == original_sha
    assert reread.as_raw_string() == b"claim payload"


@pytest.mark.property
@given(provenance_records(), provenance_records(), provenance_records())
@settings(deadline=None)
def test_provenance_composition_is_associative(
    first: Provenance,
    second: Provenance,
    third: Provenance,
) -> None:
    left = compose_provenance(
        compose_provenance(first, second, operation="fusion"),
        third,
        operation="fusion",
    )
    right = compose_provenance(
        first,
        compose_provenance(second, third, operation="fusion"),
        operation="fusion",
    )

    assert left.status == right.status
    assert left.witnesses == right.witnesses
    assert left.derived_from == right.derived_from
    assert left.operations == right.operations

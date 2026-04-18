from __future__ import annotations

from pathlib import Path

import pytest
from dulwich.objects import Blob
from dulwich.repo import MemoryRepo
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.artifacts.documents.claims import OpinionDocument, ResolutionDocument
from propstore.artifacts.documents.sources import (
    SourceTrustDocument,
    SourceTrustQualityDocument,
)
from quire.documents import DocumentSchemaError, convert_document_value
from propstore.opinion import Opinion, consensus_pair
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


def test_git_notes_round_trip_named_graph_content() -> None:
    repo = MemoryRepo()
    claim_blob = Blob.from_string(b"claim payload")
    repo.object_store.add_object(claim_blob)
    provenance = _provenance(ProvenanceStatus.MEASURED, "claim")
    encoded = encode_named_graph(provenance)

    note_commit = write_provenance_note(repo, claim_blob.id, provenance)

    assert note_commit is not None
    assert repo.refs[PROVENANCE_NOTES_REF] == note_commit
    assert read_provenance_note(repo, claim_blob.id) == provenance
    assert encode_named_graph(read_provenance_note(repo, claim_blob.id)) == encoded


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


def test_opinion_fusion_composes_provenance() -> None:
    left = Opinion(0.4, 0.2, 0.4, 0.5, provenance=_provenance(ProvenanceStatus.STATED, "left"))
    right = Opinion(0.2, 0.3, 0.5, 0.5, provenance=_provenance(ProvenanceStatus.CALIBRATED, "right"))

    fused = consensus_pair(left, right)

    assert fused.provenance is not None
    assert fused.provenance.status is ProvenanceStatus.CALIBRATED
    assert [w.source_artifact_code for w in fused.provenance.witnesses] == ["claim:left", "claim:right"]
    assert fused.provenance.operations == ("fusion",)


def test_source_trust_status_is_mandatory_at_document_boundary() -> None:
    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {"prior_base_rate": 0.5, "quality": {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5}},
            SourceTrustDocument,
            source="source.yaml",
        )

    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5},
            SourceTrustQualityDocument,
            source="source.yaml",
        )


def test_source_trust_status_round_trips() -> None:
    trust = SourceTrustDocument(
        status=ProvenanceStatus.DEFAULTED,
        prior_base_rate=0.5,
        quality=SourceTrustQualityDocument(
            status=ProvenanceStatus.VACUOUS,
            b=0.0,
            d=0.0,
            u=1.0,
            a=0.5,
        ),
        derived_from=(),
    )

    assert trust.to_payload() == {
        "status": "defaulted",
        "prior_base_rate": 0.5,
        "quality": {
            "status": "vacuous",
            "b": 0.0,
            "d": 0.0,
            "u": 1.0,
            "a": 0.5,
        },
    }


def test_opinion_document_requires_provenance() -> None:
    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5},
            OpinionDocument,
            source="stances.yaml",
        )


def test_resolution_rejects_scalar_opinion_fields() -> None:
    with pytest.raises(DocumentSchemaError):
        convert_document_value(
            {
                "method": "nli",
                "opinion_belief": 0.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 0.0,
                "opinion_base_rate": 0.5,
            },
            ResolutionDocument,
            source="stances.yaml",
        )


def test_resolution_uses_single_opinion_document_with_provenance() -> None:
    resolution = ResolutionDocument(
        method="nli",
        confidence=0.5,
        opinion=OpinionDocument(
            b=0.0,
            d=0.0,
            u=1.0,
            a=0.5,
            provenance=_provenance(ProvenanceStatus.VACUOUS, "stance"),
        ),
    )

    payload = resolution.to_payload()

    assert set(payload) == {"method", "confidence", "opinion"}
    assert payload["opinion"]["provenance"]["status"] == "vacuous"
    assert "opinion_belief" not in payload

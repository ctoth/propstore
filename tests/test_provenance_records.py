from __future__ import annotations

import pytest

import propstore.provenance as provenance


def test_projection_frame_record_is_exported() -> None:
    assert provenance.ProjectionFrameProvenanceRecord


def test_projection_frame_requires_uri_identity() -> None:
    with pytest.raises(ValueError, match="URI"):
        provenance.ProjectionFrameProvenanceRecord(
            frame_id="projection-frame-1",
            backend="z3",
            projected_at="2026-04-25T19:50:00Z",
            source_assertion_ids=("ps:assertion:a",),
        )


def test_projection_frame_canonicalizes_unordered_inputs() -> None:
    first = provenance.ProjectionFrameProvenanceRecord(
        frame_id="urn:projection:frame",
        backend="z3",
        projected_at="2026-04-25T19:50:00Z",
        source_assertion_ids=("ps:assertion:b", "ps:assertion:a", "ps:assertion:b"),
    )
    second = provenance.ProjectionFrameProvenanceRecord(
        frame_id="urn:projection:frame",
        backend="z3",
        projected_at="2026-04-25T19:50:00Z",
        source_assertion_ids=("ps:assertion:a", "ps:assertion:b"),
    )

    assert first == second
    assert first.source_assertion_ids == ("ps:assertion:a", "ps:assertion:b")
    assert first.identity_payload() == second.identity_payload()

    with pytest.raises(ValueError, match="source assertion"):
        provenance.ProjectionFrameProvenanceRecord(
            frame_id="urn:projection:empty",
            backend="z3",
            projected_at="2026-04-25T19:50:00Z",
            source_assertion_ids=(),
        )


def test_import_side_provenance_records_are_gone() -> None:
    """The import records were a second spelling of ``Provenance`` (2026-07-14).

    Import provenance rides the git note as a ``Provenance`` whose witnesses now
    carry the source version and content hash; nothing mirrors that on a parallel
    frozen dataclass.
    """

    for name in (
        "ImportRunProvenanceRecord",
        "SourceVersionProvenanceRecord",
        "LicenseProvenanceRecord",
        "ExternalStatementProvenanceRecord",
        "ExternalInferenceProvenanceRecord",
        "ExternalStatementAttitude",
    ):
        assert not hasattr(provenance, name), f"{name} must not be reintroduced"

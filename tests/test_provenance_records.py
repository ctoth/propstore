from __future__ import annotations

import pytest

import propstore.provenance as provenance


def test_required_provenance_record_types_are_exported() -> None:
    assert provenance.SourceVersionProvenanceRecord
    assert provenance.LicenseProvenanceRecord
    assert provenance.ImportRunProvenanceRecord
    assert provenance.ProjectionFrameProvenanceRecord
    assert provenance.ExternalStatementProvenanceRecord
    assert provenance.ExternalInferenceProvenanceRecord
    assert provenance.ExternalStatementAttitude


def test_source_version_record_requires_content_hash() -> None:
    with pytest.raises(ValueError, match="content hash"):
        provenance.SourceVersionProvenanceRecord(
            source_id="urn:source:paper",
            version_id="2026-04-25",
            content_hash="",
            retrieved_at="2026-04-25T19:50:00Z",
        )


def test_license_and_activity_records_require_uri_identity() -> None:
    with pytest.raises(ValueError, match="URI"):
        provenance.LicenseProvenanceRecord(
            license_id="cc-by-4.0",
            label="CC BY 4.0",
        )

    source = _source_version()
    license_record = _license()

    with pytest.raises(ValueError, match="URI"):
        provenance.ImportRunProvenanceRecord(
            run_id="import-run-1",
            importer_id="urn:agent:importer",
            imported_at="2026-04-25T19:50:00Z",
            source=source,
            license=license_record,
        )


def test_statement_attitude_separates_asserted_from_quoted() -> None:
    asserted = provenance.ExternalStatementProvenanceRecord(
        statement_id="urn:statement:1",
        source=_source_version(),
        locator="page:4",
        attitude=provenance.ExternalStatementAttitude.ASSERTED,
        authority_id="urn:authority:author",
    )
    quoted = provenance.ExternalStatementProvenanceRecord(
        statement_id="urn:statement:1",
        source=_source_version(),
        locator="page:4",
        attitude=provenance.ExternalStatementAttitude.QUOTED,
        authority_id="urn:authority:author",
    )

    assert asserted.identity_payload() != quoted.identity_payload()
    assert asserted.to_payload()["attitude"] == "asserted"
    assert quoted.to_payload()["attitude"] == "quoted"


def test_projection_and_inference_records_canonicalize_unordered_inputs() -> None:
    first_projection = provenance.ProjectionFrameProvenanceRecord(
        frame_id="urn:projection:frame",
        backend="z3",
        projected_at="2026-04-25T19:50:00Z",
        source_assertion_ids=("ps:assertion:b", "ps:assertion:a", "ps:assertion:b"),
    )
    second_projection = provenance.ProjectionFrameProvenanceRecord(
        frame_id="urn:projection:frame",
        backend="z3",
        projected_at="2026-04-25T19:50:00Z",
        source_assertion_ids=("ps:assertion:a", "ps:assertion:b"),
    )

    assert first_projection == second_projection
    assert first_projection.to_payload()["source_assertion_ids"] == [
        "ps:assertion:a",
        "ps:assertion:b",
    ]

    with pytest.raises(ValueError, match="source assertion"):
        provenance.ProjectionFrameProvenanceRecord(
            frame_id="urn:projection:empty",
            backend="z3",
            projected_at="2026-04-25T19:50:00Z",
            source_assertion_ids=(),
        )

    first_inference = provenance.ExternalInferenceProvenanceRecord(
        inference_id="urn:inference:1",
        engine="external-solver",
        inferred_at="2026-04-25T19:50:00Z",
        premise_statement_ids=("urn:statement:b", "urn:statement:a"),
        conclusion_statement_id="urn:statement:c",
    )
    second_inference = provenance.ExternalInferenceProvenanceRecord(
        inference_id="urn:inference:1",
        engine="external-solver",
        inferred_at="2026-04-25T19:50:00Z",
        premise_statement_ids=("urn:statement:a", "urn:statement:b"),
        conclusion_statement_id="urn:statement:c",
    )

    assert first_inference == second_inference
    assert first_inference.to_payload()["premise_statement_ids"] == [
        "urn:statement:a",
        "urn:statement:b",
    ]


def _source_version() -> provenance.SourceVersionProvenanceRecord:
    return provenance.SourceVersionProvenanceRecord(
        source_id="urn:source:paper",
        version_id="2026-04-25",
        content_hash="sha256:abc123",
        retrieved_at="2026-04-25T19:50:00Z",
    )


def _license() -> provenance.LicenseProvenanceRecord:
    return provenance.LicenseProvenanceRecord(
        license_id="urn:license:cc-by-4.0",
        label="CC BY 4.0",
        uri="https://creativecommons.org/licenses/by/4.0/",
    )

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

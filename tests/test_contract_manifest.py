from __future__ import annotations

from pathlib import Path

from propstore.contracts import (
    CONTRACT_MANIFEST_PATH,
    build_propstore_contract_manifest,
    iter_artifact_families,
)


def test_every_artifact_family_has_contract_version() -> None:
    missing = [
        family.name
        for family in iter_artifact_families()
        if family.contract_version is None
    ]

    assert missing == []


def test_contract_manifest_covers_documents_and_artifact_families() -> None:
    manifest = build_propstore_contract_manifest()
    keys = {entry.key for entry in manifest.contracts}

    assert "document_schema:ConceptDocument" in keys
    assert "document_schema:ClaimsFileDocument" in keys
    assert "artifact_family:concept_file" in keys
    assert "artifact_family:source_document" in keys


def test_checked_in_contract_manifest_is_current() -> None:
    expected = Path(CONTRACT_MANIFEST_PATH).read_bytes()
    actual = build_propstore_contract_manifest().to_yaml()

    assert actual == expected

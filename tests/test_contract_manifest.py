from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from quire.contracts import ContractManifest, check_contract_manifest

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


def test_contract_manifest_changes_require_version_bumps_against_head() -> None:
    relative_path = Path(CONTRACT_MANIFEST_PATH).relative_to(Path.cwd()).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        pytest.skip("checked-in contract manifest is not available from git HEAD")

    previous = ContractManifest.from_yaml(result.stdout)
    current = build_propstore_contract_manifest()

    check_contract_manifest(previous, current)

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from quire.contracts import ContractManifest, check_contract_manifest

from propstore.contracts import (
    CONTRACT_MANIFEST_PATH,
    build_propstore_contract_manifest,
    iter_artifact_families,
    iter_claim_type_contracts,
    iter_semantic_foreign_keys,
)
from propstore.families.identity.claims import (
    CLAIM_SOURCE_LOCAL_FIELDS,
    CLAIM_VERSION_ID_EXCLUDED_FIELDS,
)
from propstore.families.identity.concepts import CONCEPT_VERSION_ID_EXCLUDED_FIELDS


def test_every_artifact_family_has_contract_version() -> None:
    missing = [
        family.name
        for family in iter_artifact_families()
        if family.contract_version is None
    ]

    assert missing == []


def test_every_semantic_foreign_key_has_contract_version() -> None:
    missing = [
        spec.name
        for spec in iter_semantic_foreign_keys()
        if spec.contract_version is None
    ]

    assert missing == []


def test_every_claim_type_contract_has_contract_version() -> None:
    missing = [
        contract.claim_type.value
        for contract in iter_claim_type_contracts()
        if contract.contract_version is None
    ]

    assert missing == []


def test_contract_manifest_covers_documents_and_artifact_families() -> None:
    manifest = build_propstore_contract_manifest()
    keys = {entry.key for entry in manifest.contracts}

    assert "document_schema:ConceptDocument" in keys
    assert "document_schema:ClaimsFileDocument" in keys
    assert "document_schema:PredicatesFileDocument" in keys
    assert "document_schema:RulesFileDocument" in keys
    assert "artifact_family:concept_file" in keys
    assert "artifact_family:source_document" in keys
    assert "artifact_family:predicate_file" in keys
    assert "artifact_family:rule_file" in keys
    assert "family-registry:propstore" in keys
    assert "family:concepts" in keys
    assert "family:claims" in keys
    assert "family:predicates" in keys
    assert "family:rules" in keys
    assert "foreign_key:claim_concept" in keys
    assert "foreign_key:concept_parameterization_canonical_claim" in keys
    assert "claim_type_contract:parameter" in keys
    assert "claim_type_contract:algorithm" in keys


def test_artifact_family_contract_callbacks_are_named() -> None:
    manifest = build_propstore_contract_manifest()
    offenders = [
        (entry.name, field, callback)
        for entry in manifest.contracts
        if entry.kind == "artifact_family"
        for field, callback in entry.body.items()
        if isinstance(callback, str) and "<lambda>" in callback
    ]

    assert offenders == []


def test_claim_and_concept_family_contracts_include_identity_policy() -> None:
    manifest = build_propstore_contract_manifest()
    entries = {entry.key: entry for entry in manifest.contracts}

    claim_policy = entries["family:claims"].body["identity_policy"]
    assert claim_policy["artifact_id_function"] == (
        "propstore.families.identity.claims.derive_claim_artifact_id"
    )
    assert claim_policy["version_id_function"] == (
        "propstore.families.identity.claims.compute_claim_version_id"
    )
    assert claim_policy["canonical_payload_function"] == (
        "propstore.families.identity.claims.canonicalize_claim_for_version"
    )
    assert claim_policy["normalize_payload_function"] == (
        "propstore.families.identity.claims.normalize_canonical_claim_payload"
    )
    assert claim_policy["logical_id_fields"] == ["logical_ids"]
    assert claim_policy["version_excluded_fields"] == list(CLAIM_VERSION_ID_EXCLUDED_FIELDS)
    assert claim_policy["source_local_fields"] == list(CLAIM_SOURCE_LOCAL_FIELDS)

    concept_policy = entries["family:concepts"].body["identity_policy"]
    assert concept_policy["artifact_id_function"] == (
        "propstore.families.identity.concepts.derive_concept_artifact_id"
    )
    assert concept_policy["version_id_function"] == (
        "propstore.families.identity.concepts.compute_concept_version_id"
    )
    assert concept_policy["canonical_payload_function"] == (
        "propstore.families.identity.concepts.canonicalize_concept_for_version"
    )
    assert concept_policy["normalize_payload_function"] == (
        "propstore.families.identity.concepts.normalize_canonical_concept_payload"
    )
    assert concept_policy["logical_id_fields"] == ["logical_ids"]
    assert concept_policy["version_excluded_fields"] == list(CONCEPT_VERSION_ID_EXCLUDED_FIELDS)
    assert concept_policy["source_local_fields"] == []


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

    try:
        previous = ContractManifest.from_yaml(result.stdout)
    except ValueError as exc:
        pytest.skip(f"HEAD contract manifest predates current Quire manifest invariants: {exc}")
    current = build_propstore_contract_manifest()

    check_contract_manifest(previous, current)

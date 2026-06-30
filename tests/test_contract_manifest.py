"""Drift gate for the charter-derived semantic-contract manifest.

Retargeted from the feature-peak ``test_contract_manifest`` to the rewrite's
charter-derivation thesis (PLAN.md §12.6): the manifest no longer carries
hand-authored ``document_schema`` / ``artifact_family`` / ``foreign_key`` entries.
Those bodies fold into the registry's charter-derived ``family-registry`` /
``family`` entries (the FK graph lives inside each ``family`` body). What this
module still pins by hand — and therefore version-gates — is the claim-type and
semantic pass / stage pipeline contract.
"""

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
    iter_semantic_pass_classes,
    iter_semantic_stage_contracts,
)


def test_every_artifact_family_has_contract_version() -> None:
    missing = [
        family.name
        for family in iter_artifact_families()
        if family.contract_version is None
    ]

    assert missing == []


def test_every_semantic_foreign_key_has_contract_version() -> None:
    missing = [
        spec.name for spec in iter_semantic_foreign_keys() if spec.contract_version is None
    ]

    assert missing == []


def test_claim_type_and_pass_and_stage_surfaces_are_non_empty() -> None:
    # The three hand-composed surfaces the manifest version-gates.
    assert iter_claim_type_contracts()
    assert iter_semantic_pass_classes()
    assert iter_semantic_stage_contracts()


def test_contract_manifest_covers_charter_and_pipeline_contracts() -> None:
    manifest = build_propstore_contract_manifest()
    keys = {entry.key for entry in manifest.contracts}

    # Charter-derived registry / family entries (the family/FK/identity bodies).
    assert "family-registry:propstore" in keys
    assert "family:claim" in keys
    assert "family:concept" in keys
    assert "family:micropublication" in keys
    # Hand-composed claim-type + pipeline entries.
    assert "claim_type_contract:parameter" in keys
    assert "claim_type_contract:algorithm" in keys
    assert "semantic_pass:claim.check" in keys
    assert "semantic_stage:claim.authored" in keys
    assert "semantic_stage:concept.checked" in keys


def test_charter_derived_bodies_are_not_re_emitted_by_hand() -> None:
    # The rewrite thesis: no standalone document_schema / artifact_family /
    # foreign_key entries — those bodies live inside the charter-derived family
    # entries instead.
    manifest = build_propstore_contract_manifest()
    kinds = {entry.kind for entry in manifest.contracts}

    assert "document_schema" not in kinds
    assert "artifact_family" not in kinds
    assert "foreign_key" not in kinds


def test_foreign_key_graph_folds_into_family_bodies() -> None:
    manifest = build_propstore_contract_manifest()
    entries = {entry.key: entry for entry in manifest.contracts}

    claim_body = entries["family:claim"].body
    edges = {(fk["source_field"], fk["target_family"]) for fk in claim_body["foreign_keys"]}

    assert ("output_concept", "concept") in edges
    assert ("context_id", "context") in edges


def test_claim_type_contract_pins_semantic_check_identity() -> None:
    manifest = build_propstore_contract_manifest()
    entries = {entry.key: entry for entry in manifest.contracts}

    algorithm = entries["claim_type_contract:algorithm"].body
    assert algorithm["semantic_checks"] == [
        "propstore.claim_contracts.AlgorithmParseCheck",
        "propstore.claim_contracts.AlgorithmUnboundNamesCheck",
    ]


def test_semantic_pass_entry_records_stage_transition() -> None:
    manifest = build_propstore_contract_manifest()
    entries = {entry.key: entry for entry in manifest.contracts}

    claim_check = entries["semantic_pass:claim.check"].body
    assert claim_check["family"] == "claim"
    assert claim_check["input_stage"] == "claim.authored"
    assert claim_check["output_stage"] == "claim.checked"


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
        pytest.skip(f"HEAD contract manifest predates current invariants: {exc}")
    current = build_propstore_contract_manifest()

    check_contract_manifest(previous, current)

"""Tests for direct repo emission of the formal merge object."""
from __future__ import annotations

import yaml

import propstore.storage as repo_module
from propstore.identity import compute_claim_version_id
from quire.git_store import GitStore
from propstore.storage import init_git_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.storage.merge_commit import create_merge_commit
from propstore.storage.snapshot import RepositorySnapshot
from tests.conftest import make_claim_identity, normalize_claims_payload


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = normalize_claims_payload({
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    })
    return yaml.dump(doc, sort_keys=False).encode()


def _obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": concepts,
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _param_claim(
    cid: str,
    concept: str,
    value: float,
    unit: str = "K",
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": unit,
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def _claim_yaml_with_explicit_identities(claims: list[dict], paper: str = "test_paper") -> bytes:
    normalized = normalize_claims_payload({
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    })
    rewritten_claims: list[dict] = []
    for original, normalized_claim in zip(claims, normalized["claims"], strict=True):
        merged = dict(normalized_claim)
        if "artifact_id" in original:
            merged["artifact_id"] = original["artifact_id"]
        if "logical_ids" in original:
            merged["logical_ids"] = original["logical_ids"]
        merged["version_id"] = compute_claim_version_id(merged)
        rewritten_claims.append(merged)
    normalized["claims"] = rewritten_claims
    return yaml.dump(normalized, sort_keys=False).encode()


def _snapshot(kr: GitStore) -> RepositorySnapshot:
    if kr.root is None:
        raise ValueError("test snapshot requires a filesystem-backed git store")
    return RepositorySnapshot(Repository(kr.root))


def test_build_merge_framework_conflict_emits_mutual_attack(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left: modify claim1",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 2
    claim_ids = {argument.claim_id for argument in merge.arguments}
    artifact_id = make_claim_identity("claim1", namespace="test_paper")["artifact_id"]
    assert all(claim_id.startswith(f"{artifact_id}__") for claim_id in claim_ids)

    left_id, right_id = sorted(claim_ids)
    assert (left_id, right_id) in merge.framework.attacks
    assert (right_id, left_id) in merge.framework.attacks
    assert (left_id, right_id) not in merge.framework.ignorance
    assert (right_id, left_id) not in merge.framework.ignorance


def test_build_merge_framework_phi_node_emits_ignorance(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/phi"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 300.0, conditions=["temp > 300"])]
            )
        },
        "left: high-temp value",
    )
    kr.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])]
            )
        },
        "right: low-temp value",
        branch=branch_name,
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 2
    claim_ids = {argument.claim_id for argument in merge.arguments}
    left_id, right_id = sorted(claim_ids)
    assert (left_id, right_id) in merge.framework.ignorance
    assert (right_id, left_id) in merge.framework.ignorance
    assert (left_id, right_id) not in merge.framework.attacks
    assert (right_id, left_id) not in merge.framework.attacks


def test_build_merge_framework_compatible_one_sided_modification_emits_single_argument(
    tmp_path,
):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/compat"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 999.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge = build_merge_framework(_snapshot(kr), "master", branch_name)

    assert len(merge.arguments) == 1
    emitted = merge.arguments[0]
    assert emitted.claim_id == make_claim_identity("claim1", namespace="test_paper")["artifact_id"]
    assert emitted.claim["value"] == 999.0
    assert emitted.branch_origins == (branch_name,)
    assert merge.framework.attacks == frozenset()
    assert merge.framework.ignorance == frozenset()


def test_create_merge_commit_keeps_divergent_same_artifact_versions_out_of_materialized_claims(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/provenance"
    kr.create_branch(branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left: modify claim1",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)

    from propstore.claims import claim_file_payload
    from tests.family_helpers import load_claim_files

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")

    materialized_claims = [
        claim
        for claim_file in claim_files
        for claim in claim_file_payload(claim_file).get("claims", [])
    ]
    assert materialized_claims == []

    manifest = yaml.safe_load((kr.tree(commit=merge_sha) / "merge" / "manifest.yaml").read_text())
    manifest_arguments = manifest["merge"]["arguments"]
    assert len(manifest_arguments) == 2
    assert all(row["materialized"] is False for row in manifest_arguments)
    assert {row["artifact_id"] for row in manifest_arguments} == {
        make_claim_identity("claim1", namespace="test_paper")["artifact_id"]
    }


def test_repo_public_merge_surface_excludes_bridge_helpers() -> None:
    assert not hasattr(repo_module, "make_branch_assumption")
    assert not hasattr(repo_module, "branch_nogoods_from_merge")
    assert not hasattr(repo_module, "inject_branch_stances")


def test_create_merge_commit_records_semantic_candidates_in_manifest(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/candidates"
    kr.create_branch(branch_name, source_commit=base_sha)

    left_claim = {
        "id": "claim_a",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "left_paper", "page": 1},
        "artifact_id": "ps:claim:leftcandidate0001",
        "logical_ids": [{"namespace": "left_paper", "value": "claim_a"}],
    }
    right_claim = {
        "id": "claim_b",
        "type": "observation",
        "statement": "Equivalent observation",
        "concepts": ["concept_x"],
        "provenance": {"paper": "right_paper", "page": 1},
        "artifact_id": "ps:claim:rightcandidate0001",
        "logical_ids": [{"namespace": "right_paper", "value": "claim_b"}],
    }

    kr.commit_files(
        {"claims/left.yaml": _claim_yaml_with_explicit_identities([left_claim], paper="left_paper")},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml_with_explicit_identities([right_claim], paper="right_paper")},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(_snapshot(kr), "master", branch_name)
    manifest = yaml.safe_load((kr.tree(commit=merge_sha) / "merge" / "manifest.yaml").read_text())

    assert manifest["merge"]["semantic_candidates"] == [
        [
            "ps:claim:leftcandidate0001",
            "ps:claim:rightcandidate0001",
        ]
    ]
    assert manifest["merge"]["semantic_candidate_details"] == [
        {
            "claim_ids": [
                "ps:claim:leftcandidate0001",
                "ps:claim:rightcandidate0001",
            ],
            "logical_ids": ["left_paper:claim_a", "right_paper:claim_b"],
            "artifact_ids": [
                "ps:claim:leftcandidate0001",
                "ps:claim:rightcandidate0001",
            ],
            "arguments": [
                {
                    "claim_id": "ps:claim:leftcandidate0001",
                    "logical_id": "left_paper:claim_a",
                    "artifact_id": "ps:claim:leftcandidate0001",
                    "branch_origins": ["master"],
                    "source_paper": "left_paper",
                },
                {
                    "claim_id": "ps:claim:rightcandidate0001",
                    "logical_id": "right_paper:claim_b",
                    "artifact_id": "ps:claim:rightcandidate0001",
                    "branch_origins": [branch_name],
                    "source_paper": "right_paper",
                },
            ],
        }
    ]

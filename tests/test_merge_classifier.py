"""Regression tests for the new repository merge surface."""
from __future__ import annotations

import yaml

from propstore.repo import KnowledgeRepo
from propstore.repo.branch import create_branch
from propstore.repo.merge_classifier import build_merge_framework
from propstore.repo.merge_commit import create_merge_commit


def _claim_yaml(claims: list[dict], paper: str = "test_paper") -> bytes:
    doc = {
        "source": {
            "paper": paper,
            "extraction_model": "test",
            "extraction_date": "2026-01-01",
        },
        "claims": claims,
    }
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
    *,
    conditions: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": cid,
        "type": "parameter",
        "concept": concept,
        "value": value,
        "unit": "K",
        "concepts": [concept],
        "provenance": {"paper": "test_paper", "page": 1},
    }
    if conditions:
        claim["conditions"] = conditions
    return claim


def test_identical_claims_collapse_to_one_emitted_argument(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/test"
    create_branch(kr, branch_name, source_commit=base_sha)

    merge = build_merge_framework(kr, "master", branch_name)

    assert len(merge.arguments) == 1
    assert merge.arguments[0].claim_id == "claim1"
    assert merge.arguments[0].branch_origins == ("master", branch_name)


def test_syntax_independence_claim_order(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    claim_a = _obs_claim("claimA", "A", ["concept_a"])
    claim_b = _obs_claim("claimB", "B", ["concept_b"])
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([claim_a, claim_b])},
        "seed",
    )
    branch_name = "paper/reorder"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([claim_b, claim_a])},
        "reorder",
    )

    merge = build_merge_framework(kr, "master", branch_name)
    emitted = {argument.claim_id for argument in merge.arguments}
    assert emitted == {"claimA", "claimB"}


def test_syntax_independence_filename(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    claims = [_obs_claim("claimA", "Observation A", ["concept_a"])]
    base_sha = kr.commit_files(
        {"claims/original.yaml": _claim_yaml(claims)},
        "seed",
    )
    branch_name = "paper/rename"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_batch(
        adds={"claims/renamed.yaml": _claim_yaml(claims)},
        deletes=["claims/original.yaml"],
        message="rename file",
    )

    merge = build_merge_framework(kr, "master", branch_name)
    assert len(merge.arguments) == 1
    assert merge.arguments[0].claim_id == "claimA"


def test_merge_commit_has_two_parents(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/merge_test"
    create_branch(kr, branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)
    commit_obj = kr._repo[merge_sha.encode()]
    assert len(commit_obj.parents) == 2


def test_merge_commit_preserves_both_disjoint_additions(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/preserve"
    create_branch(kr, branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left only", ["concept_a"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right only", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    from propstore.validate_claims import load_claim_files

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    all_claim_ids = {
        claim["id"]
        for claim_file in claim_files
        for claim in claim_file.data.get("claims", [])
    }
    assert "claimL" in all_claim_ids
    assert "claimR" in all_claim_ids


def test_merge_commit_valid_claims(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/base.yaml": _claim_yaml([_obs_claim("claim1", "Base", ["concept_x"])])},
        "seed",
    )
    branch_name = "paper/valid"
    create_branch(kr, branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/left.yaml": _claim_yaml([_obs_claim("claimL", "Left", ["concept_a"])])},
        "left",
    )
    kr.commit_files(
        {"claims/right.yaml": _claim_yaml([_obs_claim("claimR", "Right", ["concept_b"])])},
        "right",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    from propstore.validate_claims import load_claim_files, validate_claims

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")
    result = validate_claims(
        claim_files,
        concept_registry={},
    )
    assert not result.errors


def test_conflict_merge_is_deterministic(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    create_branch(kr, branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    merge_sha_a = create_merge_commit(kr, "master", branch_name, target_branch="merge_a")
    merge_sha_b = create_merge_commit(kr, "master", branch_name, target_branch="merge_b")

    commit_a = kr._repo[merge_sha_a.encode()]
    commit_b = kr._repo[merge_sha_b.encode()]
    assert commit_a.tree == commit_b.tree


def test_merge_commit_preserves_branch_origin_provenance(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    create_branch(kr, branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    merge = build_merge_framework(kr, "master", branch_name)
    expected_origins = {
        argument.claim_id: list(argument.branch_origins)
        for argument in merge.arguments
    }

    merge_sha = create_merge_commit(kr, "master", branch_name)

    manifest_path = kr.tree(commit=merge_sha) / "merge" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    observed_origins = {
        row["claim_id"]: row["branch_origins"]
        for row in manifest["merge"]["arguments"]
    }
    assert observed_origins == expected_origins

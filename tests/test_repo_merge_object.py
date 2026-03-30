"""Tests for direct repo emission of the formal merge object."""
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


def test_build_merge_framework_conflict_emits_mutual_attack(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left: modify claim1",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge = build_merge_framework(kr, "master", branch_name)

    assert len(merge.arguments) == 2
    claim_ids = {argument.claim_id for argument in merge.arguments}
    assert all(claim_id.startswith("claim1__") for claim_id in claim_ids)

    left_id, right_id = sorted(claim_ids)
    assert (left_id, right_id) in merge.framework.attacks
    assert (right_id, left_id) in merge.framework.attacks
    assert (left_id, right_id) not in merge.framework.ignorance
    assert (right_id, left_id) not in merge.framework.ignorance


def test_build_merge_framework_phi_node_emits_ignorance(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/phi"
    create_branch(kr, branch_name, source_commit=base_sha)

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

    merge = build_merge_framework(kr, "master", branch_name)

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
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/compat"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 999.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge = build_merge_framework(kr, "master", branch_name)

    assert len(merge.arguments) == 1
    emitted = merge.arguments[0]
    assert emitted.claim_id == "claim1"
    assert emitted.claim["value"] == 999.0
    assert emitted.branch_origins == (branch_name,)
    assert merge.framework.attacks == frozenset()
    assert merge.framework.ignorance == frozenset()


def test_create_merge_commit_preserves_conflicting_versions_with_provenance(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/provenance"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left: modify claim1",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right: modify claim1",
        branch=branch_name,
    )

    merge_sha = create_merge_commit(kr, "master", branch_name)

    from propstore.validate_claims import load_claim_files

    claim_files = load_claim_files(kr.tree(commit=merge_sha) / "claims")

    conflict_versions = []
    for claim_file in claim_files:
        for claim in claim_file.data.get("claims", []):
            if claim["id"].startswith("claim1__"):
                conflict_versions.append(claim)

    assert len(conflict_versions) == 2
    origins = {claim["provenance"]["branch_origin"] for claim in conflict_versions}
    assert origins == {"master", branch_name}

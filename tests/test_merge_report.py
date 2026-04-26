"""Tests for repo-facing merge query/report helpers."""
from __future__ import annotations

import yaml

from propstore.families.identity.claims import compute_claim_version_id
from propstore.families.identity.concepts import derive_concept_artifact_id
from quire.git_store import GitStore
from propstore.storage import init_git_store
from propstore.repository import Repository
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import summarize_merge_framework
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


def test_merge_report_surfaces_conflict_query_state(tmp_path):
    kr = init_git_store(tmp_path / "knowledge")
    concept_id = derive_concept_artifact_id("propstore", "concept_x")
    base_sha = kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 250.0)])},
        "seed",
    )
    branch_name = "paper/conflict"
    kr.create_branch(branch_name, source_commit=base_sha)
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 300.0)])},
        "left",
    )
    kr.commit_files(
        {"claims/shared.yaml": _claim_yaml([_param_claim("claim1", "concept_x", 150.0)])},
        "right",
        branch=branch_name,
    )

    report = summarize_merge_framework(
        build_merge_framework(_snapshot(kr), "master", branch_name),
        semantics="grounded",
    )

    assert report["surface"] == "formal_merge_report"
    assert report["framework_type"] == "partial_argumentation_framework"
    assert report["completion_count"] == 1
    assert len(report["attacks"]) == 2
    assert report["relation_counts"] == {
        "attack": 2,
        "ignorance": 0,
        "non_attack": 2,
    }
    assert report["skeptical"] == []
    assert report["credulous"] == []
    artifact_id = make_claim_identity("claim1", namespace="test_paper")["artifact_id"]
    assert report["canonical_groups"] == {
        "test_paper:claim1": sorted(report["arguments"]),
    }
    assert len(report["argument_details"]) == 2
    for detail in report["argument_details"]:
        assert detail["assertion_id"] in report["arguments"]
        assert detail["assertion_id"].startswith("ps:assertion:")
        assert detail["canonical_claim_id"] == "test_paper:claim1"
        assert detail["artifact_id"] == artifact_id
        assert detail["logical_id"] == "test_paper:claim1"
        assert detail["concept_id"] == concept_id
        assert detail["branch_origins"]
        assert detail["provenance"]["branch_origin"] in detail["branch_origins"]
        assert detail["credulously_accepted"] is False
        assert detail["skeptically_accepted"] is False


def test_merge_report_surfaces_ignorance_query_state(tmp_path):
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
        "left",
    )
    kr.commit_files(
        {
            "claims/shared.yaml": _claim_yaml(
                [_param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])]
            )
        },
        "right",
        branch=branch_name,
    )

    report = summarize_merge_framework(
        build_merge_framework(_snapshot(kr), "master", branch_name),
        semantics="grounded",
    )

    assert report["surface"] == "formal_merge_report"
    assert report["framework_type"] == "partial_argumentation_framework"
    assert report["completion_count"] == 4
    assert len(report["ignorance"]) == 2
    assert report["relation_counts"] == {
        "attack": 0,
        "ignorance": 2,
        "non_attack": 2,
    }
    assert report["skeptical"] == []
    assert len(report["credulous"]) == 2
    assert report["canonical_groups"] == {
        "test_paper:claim1": sorted(report["arguments"]),
    }
    assert len(report["argument_details"]) == 2
    detail_by_id = {
        detail["assertion_id"]: detail for detail in report["argument_details"]
    }
    for assertion_id in report["credulous"]:
        assert report["statuses"][assertion_id]["credulously_accepted"] is True
        assert detail_by_id[assertion_id]["credulously_accepted"] is True
        assert detail_by_id[assertion_id]["provenance"]["branch_origin"] in detail_by_id[assertion_id]["branch_origins"]


def test_merge_report_collapses_duplicate_assertion_identity_without_candidate_bucket(tmp_path):
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

    report = summarize_merge_framework(
        build_merge_framework(_snapshot(kr), "master", branch_name),
        semantics="grounded",
    )

    assert len(report["arguments"]) == 1
    assert report["arguments"][0].startswith("ps:assertion:")
    assert report["semantic_candidates"] == []
    assert report["semantic_candidate_details"] == []

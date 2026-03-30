"""Tests for repo-facing merge query/report helpers."""
from __future__ import annotations

import yaml

from propstore.repo import KnowledgeRepo
from propstore.repo.branch import create_branch
from propstore.repo.merge_classifier import build_merge_framework
from propstore.repo.merge_report import summarize_merge_framework


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


def test_merge_report_surfaces_conflict_query_state(tmp_path):
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

    report = summarize_merge_framework(
        build_merge_framework(kr, "master", branch_name),
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
    assert report["canonical_groups"] == {
        "claim1": sorted(report["arguments"]),
    }
    assert len(report["argument_details"]) == 2
    for detail in report["argument_details"]:
        assert detail["claim_id"] in report["arguments"]
        assert detail["canonical_claim_id"] == "claim1"
        assert detail["concept_id"] == "concept_x"
        assert detail["branch_origins"]
        assert detail["provenance"]["branch_origin"] in detail["branch_origins"]
        assert detail["credulously_accepted"] is False
        assert detail["skeptically_accepted"] is False


def test_merge_report_surfaces_ignorance_query_state(tmp_path):
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
        build_merge_framework(kr, "master", branch_name),
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
        "claim1": sorted(report["arguments"]),
    }
    assert len(report["argument_details"]) == 2
    detail_by_id = {
        detail["claim_id"]: detail for detail in report["argument_details"]
    }
    for claim_id in report["credulous"]:
        assert report["statuses"][claim_id]["credulously_accepted"] is True
        assert detail_by_id[claim_id]["credulously_accepted"] is True
        assert detail_by_id[claim_id]["provenance"]["branch_origin"] in detail_by_id[claim_id]["branch_origins"]

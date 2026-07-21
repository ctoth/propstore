"""Repo-facing merge query/report helpers over plain claim sets (Phase 6c)."""

from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import summarize_merge_framework
from tests.merge_helpers import param_claim


def test_merge_report_surfaces_conflict_query_state() -> None:
    base = [param_claim("claim1", "concept_x", 250.0)]
    merge = build_merge_framework(
        {
            "master": [param_claim("claim1", "concept_x", 300.0)],
            "paper/conflict": [param_claim("claim1", "concept_x", 150.0)],
        },
        "master",
        "paper/conflict",
        base_claims=base,
    )
    report = summarize_merge_framework(merge, semantics="grounded")

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
        assert detail["assertion_id"] in report["arguments"]
        assert detail["assertion_id"].startswith("ps:assertion:")
        assert detail["canonical_claim_id"] == "claim1"
        assert detail["artifact_id"] == "claim1"
        assert detail["logical_id"] == "claim1"
        assert detail["concept_id"] == "concept_x"
        assert detail["branch_origins"]
        assert detail["provenance"]["branch_origin"] in detail["branch_origins"]
        assert detail["credulously_accepted"] is False
        assert detail["skeptically_accepted"] is False


def test_merge_report_surfaces_ignorance_query_state() -> None:
    base = [param_claim("claim1", "concept_x", 250.0)]
    merge = build_merge_framework(
        {
            "master": [
                param_claim("claim1", "concept_x", 300.0, conditions=["temp > 300"])
            ],
            "paper/phi": [
                param_claim("claim1", "concept_x", 150.0, conditions=["temp < 200"])
            ],
        },
        "master",
        "paper/phi",
        base_claims=base,
    )
    report = summarize_merge_framework(merge, semantics="grounded")

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
        detail["assertion_id"]: detail for detail in report["argument_details"]
    }
    for assertion_id in report["credulous"]:
        assert report["statuses"][assertion_id]["credulously_accepted"] is True
        assert detail_by_id[assertion_id]["credulously_accepted"] is True
        provenance = detail_by_id[assertion_id]["provenance"]
        assert (
            provenance["branch_origin"] in detail_by_id[assertion_id]["branch_origins"]
        )

"""Tests for branch-local structured projection into merge summaries."""
from __future__ import annotations

import yaml

from propstore.repo import KnowledgeRepo
from propstore.repo.branch import create_branch
from propstore.repo.structured_merge import (
    build_branch_structured_summary,
    build_structured_merge_candidates,
)


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


def _stance_yaml(source_claim: str, stances: list[dict]) -> bytes:
    return yaml.dump(
        {"source_claim": source_claim, "stances": stances},
        sort_keys=False,
    ).encode()


def _obs_claim(cid: str, statement: str) -> dict:
    return {
        "id": cid,
        "type": "observation",
        "statement": statement,
        "concepts": ["concept_x"],
        "confidence": 0.5,
        "sample_size": 10,
        "provenance": {"paper": "test_paper", "page": 1},
    }


def test_branch_structured_summary_reads_branch_snapshot_stances(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
                _obs_claim("claim_b", "B"),
            ]),
            "stances/claim_a.yaml": _stance_yaml(
                "claim_a",
                [{"target": "claim_b", "type": "contradicts"}],
            ),
        },
        "seed structured branch",
    )

    summary = build_branch_structured_summary(kr, "master")

    assert summary.claim_ids == ("claim_a", "claim_b")
    assert summary.claim_provenance["claim_a"]["paper"] == "test_paper"
    assert summary.claim_provenance["claim_b"]["paper"] == "test_paper"

    claim_attack_pairs = {
        (
            summary.projection.argument_to_claim_id[attacker],
            summary.projection.argument_to_claim_id[target],
        )
        for attacker, target in summary.projection.framework.attacks
    }
    assert ("claim_a", "claim_b") in claim_attack_pairs


def test_structured_merge_candidates_reuse_identical_branch_summaries(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/structured"
    create_branch(kr, branch_name, source_commit=base_sha)

    adds = {
        "claims/claims.yaml": _claim_yaml([
            _obs_claim("claim_a", "A"),
            _obs_claim("claim_b", "B"),
        ]),
        "stances/claim_a.yaml": _stance_yaml(
            "claim_a",
            [{"target": "claim_b", "type": "contradicts"}],
        ),
    }
    kr.commit_files(adds, "left structured")
    kr.commit_files(adds, "right structured", branch=branch_name)

    summary = build_branch_structured_summary(kr, "master")
    branch_summary = build_branch_structured_summary(kr, branch_name)
    candidates = build_structured_merge_candidates(kr, "master", branch_name, operator="sum")

    assert summary.content_signature == branch_summary.content_signature
    assert candidates == [summary.projection.framework]


def test_branch_structured_summary_is_stable_on_repeated_builds(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
                _obs_claim("claim_b", "B"),
            ]),
            "stances/claim_a.yaml": _stance_yaml(
                "claim_a",
                [{"target": "claim_b", "type": "contradicts"}],
            ),
        },
        "seed structured branch",
    )

    left = build_branch_structured_summary(kr, "master")
    right = build_branch_structured_summary(kr, "master")

    assert left.claim_ids == right.claim_ids
    assert left.claim_provenance == right.claim_provenance
    assert left.content_signature == right.content_signature
    assert left.projection.framework == right.projection.framework


def test_branch_structured_summary_stays_local_to_branch_scope(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/local-only"
    create_branch(kr, branch_name, source_commit=base_sha)

    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
            ]),
        },
        "left",
    )
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
                _obs_claim("claim_b", "B"),
            ]),
            "stances/claim_a.yaml": _stance_yaml(
                "claim_a",
                [{"target": "claim_b", "type": "contradicts"}],
            ),
        },
        "right",
        branch=branch_name,
    )

    summary = build_branch_structured_summary(kr, "master")

    assert summary.claim_ids == ("claim_a",)
    assert set(summary.projection.argument_to_claim_id.values()) == {"claim_a"}
    assert summary.projection.framework.attacks == frozenset()

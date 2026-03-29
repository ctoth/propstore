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
    candidates = build_structured_merge_candidates(kr, "master", branch_name, operator="sum")

    assert candidates == [summary.projection.framework]

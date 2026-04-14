"""Tests for branch-local structured projection into merge summaries."""
from __future__ import annotations

from pathlib import Path

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.repo import KnowledgeRepo
from propstore.repo.branch import create_branch
from propstore.repo.snapshot import RepoSnapshot
from propstore.repo.structured_merge import (
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
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


def _stance_yaml(source_claim: str, stances: list[dict]) -> bytes:
    return yaml.dump(
        {"source_claim": source_claim, "stances": stances},
        sort_keys=False,
    ).encode()


def _artifact_id(local_id: str, *, paper: str = "test_paper") -> str:
    return make_claim_identity(local_id, namespace=paper)["artifact_id"]


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


def _snapshot(kr: KnowledgeRepo) -> RepoSnapshot:
    return RepoSnapshot.for_git(kr)


def test_branch_structured_summary_reads_branch_snapshot_stances(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
                _obs_claim("claim_b", "B"),
            ]),
            "stances/claim_a.yaml": _stance_yaml(
                _artifact_id("claim_a"),
                [{"target": _artifact_id("claim_b"), "type": "rebuts"}],
            ),
        },
        "seed structured branch",
    )

    summary = build_branch_structured_summary(_snapshot(kr), "master")

    assert summary.claim_ids == (_artifact_id("claim_a"), _artifact_id("claim_b"))
    assert summary.claim_provenance[_artifact_id("claim_a")]["paper"] == "test_paper"
    assert summary.claim_provenance[_artifact_id("claim_b")]["paper"] == "test_paper"
    assert summary.relation_surface == {
        "attack": "preserved_via_projection",
        "non_attack": "not_preserved_in_summary",
        "ignorance": "not_preserved_in_summary",
    }
    assert summary.lossiness == (
        "subargument_identity",
        "justification_identity",
        "preference_metadata",
        "support_metadata",
        "known_non_attack_relations",
        "ignorance_relations",
    )

    claim_attack_pairs = {
        (
            summary.projection.argument_to_claim_id[attacker],
            summary.projection.argument_to_claim_id[target],
        )
        for attacker, target in (summary.projection.framework.attacks or frozenset())
    }
    assert (_artifact_id("claim_a"), _artifact_id("claim_b")) in claim_attack_pairs


def test_structured_merge_candidates_reuse_identical_branch_summaries(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/structured"
    create_branch(kr, branch_name, source_commit=base_sha)

    adds: dict[str | Path, bytes] = {
        "claims/claims.yaml": _claim_yaml([
            _obs_claim("claim_a", "A"),
            _obs_claim("claim_b", "B"),
        ]),
        "stances/claim_a.yaml": _stance_yaml(
            _artifact_id("claim_a"),
            [{"target": _artifact_id("claim_b"), "type": "rebuts"}],
        ),
    }
    kr.commit_files(adds, "left structured")
    kr.commit_files(adds, "right structured", branch=branch_name)

    summary = build_branch_structured_summary(_snapshot(kr), "master")
    branch_summary = build_branch_structured_summary(_snapshot(kr), branch_name)
    candidates = build_structured_merge_candidates(_snapshot(kr), "master", branch_name, operator="sum")

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
                _artifact_id("claim_a"),
                [{"target": _artifact_id("claim_b"), "type": "rebuts"}],
            ),
        },
        "seed structured branch",
    )

    left = build_branch_structured_summary(_snapshot(kr), "master")
    right = build_branch_structured_summary(_snapshot(kr), "master")

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
                _artifact_id("claim_a"),
                [{"target": _artifact_id("claim_b"), "type": "rebuts"}],
            ),
        },
        "right",
        branch=branch_name,
    )

    summary = build_branch_structured_summary(_snapshot(kr), "master")

    assert summary.claim_ids == (_artifact_id("claim_a"),)
    assert set(summary.projection.argument_to_claim_id.values()) == {_artifact_id("claim_a")}
    assert summary.projection.framework.attacks == frozenset()


def test_branch_structured_summary_explicitly_marks_lossy_relation_boundary(tmp_path):
    kr = KnowledgeRepo.init(tmp_path / "knowledge")
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([
                _obs_claim("claim_a", "A"),
                _obs_claim("claim_b", "B"),
            ]),
        },
        "seed structured branch",
    )

    summary = build_branch_structured_summary(_snapshot(kr), "master")

    assert summary.relation_surface["attack"] == "preserved_via_projection"
    assert summary.relation_surface["non_attack"] == "not_preserved_in_summary"
    assert summary.relation_surface["ignorance"] == "not_preserved_in_summary"
    assert "known_non_attack_relations" in summary.lossiness
    assert "ignorance_relations" in summary.lossiness


@settings(
    deadline=None,
)
@given(
    extra_targets=st.lists(
        st.from_regex(r"claim_extra_[a-z]{1,3}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    )
)
def test_branch_structured_summary_ignores_out_of_scope_stances_in_identity(
    extra_targets: list[str],
):
    kr = KnowledgeRepo.init_memory()
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/out_of_scope"
    create_branch(kr, branch_name, source_commit=base_sha)

    base_claims = [
        _obs_claim("claim_a", "A"),
        _obs_claim("claim_b", "B"),
    ]
    in_scope_stances = [{"target": "claim_b", "type": "rebuts"}]
    extra_stances = [
        {"target": target, "type": "rebuts"}
        for target in extra_targets
    ]

    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml(base_claims),
            "stances/claim_a.yaml": _stance_yaml(
                _artifact_id("claim_a"),
                [{"target": _artifact_id("claim_b"), "type": "rebuts"}],
            ),
        },
        "left",
    )
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml(base_claims),
            "stances/claim_a.yaml": _stance_yaml(
                _artifact_id("claim_a"),
                [{"target": _artifact_id("claim_b"), "type": "rebuts"}] + extra_stances,
            ),
        },
        "right",
        branch=branch_name,
    )

    left_summary = build_branch_structured_summary(_snapshot(kr), "master")
    right_summary = build_branch_structured_summary(_snapshot(kr), branch_name)

    assert left_summary.claim_ids == right_summary.claim_ids
    assert left_summary.claim_provenance == right_summary.claim_provenance
    assert left_summary.content_signature == right_summary.content_signature
    assert left_summary.stance_rows == right_summary.stance_rows
    assert left_summary.projection.framework == right_summary.projection.framework


@settings(
    deadline=None,
)
@given(
    claim_order=st.permutations(("claim_a", "claim_b", "claim_c")),
    stance_order=st.permutations(("claim_b", "claim_c")),
)
def test_branch_structured_summary_is_order_invariant(
    claim_order: tuple[str, ...],
    stance_order: tuple[str, ...],
):
    kr = KnowledgeRepo.init_memory()
    base_sha = kr.commit_files({}, "seed")
    branch_name = "paper/order_invariant"
    create_branch(kr, branch_name, source_commit=base_sha)

    claims_by_id = {
        "claim_a": _obs_claim("claim_a", "A"),
        "claim_b": _obs_claim("claim_b", "B"),
        "claim_c": _obs_claim("claim_c", "C"),
    }
    stances = [{"target": target, "type": "rebuts"} for target in stance_order]

    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml([claims_by_id[claim_id] for claim_id in claim_order]),
            "stances/claim_a.yaml": _stance_yaml(
                _artifact_id("claim_a"),
                [{"target": _artifact_id(target), "type": "rebuts"} for target in stance_order],
            ),
        },
        "left",
    )
    kr.commit_files(
        {
            "claims/claims.yaml": _claim_yaml(
                [claims_by_id["claim_c"], claims_by_id["claim_a"], claims_by_id["claim_b"]]
            ),
            "stances/claim_a.yaml": _stance_yaml(
                _artifact_id("claim_a"),
                [
                    {"target": _artifact_id("claim_c"), "type": "rebuts"},
                    {"target": _artifact_id("claim_b"), "type": "rebuts"},
                ],
            ),
        },
        "right",
        branch=branch_name,
    )

    left_summary = build_branch_structured_summary(_snapshot(kr), "master")
    right_summary = build_branch_structured_summary(_snapshot(kr), branch_name)

    assert left_summary.claim_ids == right_summary.claim_ids
    assert left_summary.claim_provenance == right_summary.claim_provenance
    assert left_summary.content_signature == right_summary.content_signature
    assert left_summary.stance_rows == right_summary.stance_rows
    assert left_summary.projection.framework == right_summary.projection.framework

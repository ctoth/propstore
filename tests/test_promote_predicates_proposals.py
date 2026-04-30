from __future__ import annotations

import json

import pytest

from propstore.families.registry import PredicateFileRef
from propstore.proposals import UnknownProposalPath
from propstore.repository import Repository


PAPER = "Ioannidis_2005_WhyMostPublishedResearch"


def _predicate_fixture() -> str:
    return json.dumps(
        {
            "declarations": [
                {
                    "name": "sample_size",
                    "arity": 2,
                    "arg_types": ["paper_id", "int"],
                    "description": "Paper-level sample size.",
                },
                {
                    "name": "statistical_power",
                    "arity": 2,
                    "arg_types": ["paper_id", "float"],
                    "description": "Paper-level statistical power.",
                },
                {
                    "name": "pre_study_odds",
                    "arity": 2,
                    "arg_types": ["paper_id", "float"],
                    "description": "Pre-study odds of a true relationship.",
                },
                {
                    "name": "bias",
                    "arity": 2,
                    "arg_types": ["paper_id", "float"],
                    "description": "Bias probability in the study setting.",
                },
            ]
        }
    )


def _seed_proposal(monkeypatch, repo: Repository) -> str:
    from propstore.heuristic import predicate_extraction

    monkeypatch.setattr(
        predicate_extraction,
        "_llm_call",
        lambda **_kwargs: _predicate_fixture(),
    )
    result = predicate_extraction.propose_predicates_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
    )
    assert result.commit_sha is not None
    return result.commit_sha


def test_promote_predicate_proposal_writes_canonical_and_is_idempotent(
    monkeypatch,
    tmp_path,
) -> None:
    from propstore.proposals_predicates import (
        plan_predicate_proposal_promotion,
        promote_predicate_proposals,
    )

    repo = Repository.init(tmp_path / "knowledge")
    proposal_sha = _seed_proposal(monkeypatch, repo)

    plan = plan_predicate_proposal_promotion(repo, source_paper=PAPER)
    result = promote_predicate_proposals(repo, plan)

    assert result.moved == 1
    document = repo.families.predicates.require(PredicateFileRef(PAPER))
    assert [entry.id for entry in document.predicates] == [
        "sample_size",
        "statistical_power",
        "pre_study_odds",
        "bias",
    ]
    assert document.promoted_from_sha == proposal_sha

    second = plan_predicate_proposal_promotion(repo, source_paper=PAPER)
    assert second.items == ()


def test_plan_predicate_proposal_unknown_paper_raises(monkeypatch, tmp_path) -> None:
    from propstore.proposals_predicates import plan_predicate_proposal_promotion

    repo = Repository.init(tmp_path / "knowledge")
    _seed_proposal(monkeypatch, repo)

    with pytest.raises(UnknownProposalPath, match="does-not-exist"):
        plan_predicate_proposal_promotion(repo, source_paper="does-not-exist")

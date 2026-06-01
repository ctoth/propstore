from __future__ import annotations

import json

import yaml

from propstore.families.registry import PredicateProposalRef
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


def test_propose_predicates_dry_run_does_not_commit(monkeypatch, tmp_path) -> None:
    from propstore.heuristic import predicate_extraction

    repo = Repository.init(tmp_path / "knowledge")
    before = repo.git.branch_sha(predicate_extraction.predicate_proposal_branch())
    monkeypatch.setattr(
        predicate_extraction,
        "_llm_call",
        lambda **_kwargs: _predicate_fixture(),
    )

    result = predicate_extraction.propose_predicates_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
        dry_run=True,
    )

    assert result.commit_sha is None
    assert len(result.declarations) == 4
    assert (
        repo.git.branch_sha(predicate_extraction.predicate_proposal_branch()) == before
    )

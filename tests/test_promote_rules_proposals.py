from __future__ import annotations

import json

import pytest

from propstore.families.documents.predicates import PredicateDocument, PredicatesFileDocument
from propstore.families.registry import PredicateFileRef, RuleFileRef
from propstore.proposals import UnknownProposalPath
from propstore.repository import Repository


PAPER = "Ioannidis_2005_WhyMostPublishedResearch"


def _seed_predicates(repo: Repository) -> None:
    repo.families.predicates.save(
        PredicateFileRef(PAPER),
        PredicatesFileDocument(
            predicates=(
                PredicateDocument(
                    id="sample_size",
                    arity=2,
                    arg_types=("paper_id", "int"),
                    description="Paper-level sample size.",
                ),
                PredicateDocument(
                    id="bias",
                    arity=2,
                    arg_types=("paper_id", "float"),
                    description="Study-setting bias.",
                ),
            )
        ),
        message="Seed predicate vocabulary",
    )


def _rule_fixture() -> str:
    return json.dumps(
        {
            "rules": [
                {
                    "rule_id": "rule-001",
                    "rule_type": "defeasible",
                    "head": "low_trust(P)",
                    "body": ["sample_size(P, 30)", "bias(P, 0.8)"],
                    "predicates_referenced": ["sample_size/2", "bias/2"],
                    "page_reference": "Ioannidis 2005 p. 0697",
                },
                {
                    "rule_id": "rule-003",
                    "rule_type": "defeasible",
                    "head": "high_trust(P)",
                    "body": ["sample_size(P, 500)"],
                    "predicates_referenced": ["sample_size/2"],
                    "page_reference": "Ioannidis 2005 p. 0697",
                },
            ]
        }
    )


def _seed_rule_proposals(monkeypatch, repo: Repository) -> str:
    from propstore.heuristic import rule_extraction

    _seed_predicates(repo)
    monkeypatch.setattr(rule_extraction, "_llm_call", lambda **_kwargs: _rule_fixture())
    result = rule_extraction.propose_rules_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
    )
    assert result.commit_sha is not None
    return result.commit_sha


def test_promote_rule_proposals_selective_and_idempotent(monkeypatch, tmp_path) -> None:
    from propstore.proposals_rules import plan_rule_proposal_promotion, promote_rule_proposals

    repo = Repository.init(tmp_path / "knowledge")
    proposal_sha = _seed_rule_proposals(monkeypatch, repo)

    plan = plan_rule_proposal_promotion(repo, source_paper=PAPER, rule_ids=("rule-001",))
    result = promote_rule_proposals(repo, plan)

    assert result.moved == 1
    promoted = repo.families.rules.require(RuleFileRef(f"{PAPER}/rule-001"))
    assert promoted.source.paper == PAPER
    assert promoted.rules[0].id == "rule-001"
    assert promoted.promoted_from_sha == proposal_sha
    assert repo.families.rules.load(RuleFileRef(f"{PAPER}/rule-003")) is None

    second = plan_rule_proposal_promotion(repo, source_paper=PAPER, rule_ids=("rule-001",))
    assert second.items == ()


def test_plan_rule_proposal_unknown_id_raises(monkeypatch, tmp_path) -> None:
    from propstore.proposals_rules import plan_rule_proposal_promotion

    repo = Repository.init(tmp_path / "knowledge")
    _seed_rule_proposals(monkeypatch, repo)

    with pytest.raises(UnknownProposalPath, match="does-not-exist"):
        plan_rule_proposal_promotion(repo, source_paper=PAPER, rule_ids=("does-not-exist",))

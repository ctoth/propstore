from __future__ import annotations

import json

from propstore.families.documents.predicates import PredicateDocument, PredicatesFileDocument
from propstore.families.registry import PredicateFileRef, RuleProposalRef
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
                    "rule_id": "rule-unknown",
                    "rule_type": "defeasible",
                    "head": "low_trust(P)",
                    "body": ["invented_predicate(P, true)"],
                    "predicates_referenced": ["invented_predicate/2"],
                    "page_reference": "Ioannidis 2005 p. 0697",
                },
            ]
        }
    )


def test_propose_rules_writes_only_admitted_rule_proposals(monkeypatch, tmp_path) -> None:
    from propstore.heuristic import rule_extraction

    repo = Repository.init(tmp_path / "knowledge")
    _seed_predicates(repo)
    monkeypatch.setattr(rule_extraction, "_llm_call", lambda **_kwargs: _rule_fixture())

    result = rule_extraction.propose_rules_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
    )

    assert result.commit_sha is not None
    assert result.rule_ids == ("rule-001",)
    assert [rejection.rule_id for rejection in result.rejections] == ["rule-unknown"]
    assert result.rejections[0].status == "vacuous"
    assert repo.families.rules.load(rule_extraction.canonical_rule_ref(PAPER, "rule-001")) is None

    proposal = repo.families.proposal_rules.require(
        RuleProposalRef(PAPER, "rule-001"),
        commit=result.commit_sha,
    )
    assert proposal.predicates_referenced == ("sample_size/2", "bias/2")
    assert proposal.extraction_provenance.prompt_sha == rule_extraction.PROMPT_SHA
    assert proposal.page_reference == "Ioannidis 2005 p. 0697"


def test_propose_rules_dry_run_does_not_commit(monkeypatch, tmp_path) -> None:
    from propstore.heuristic import rule_extraction

    repo = Repository.init(tmp_path / "knowledge")
    _seed_predicates(repo)
    before = repo.snapshot.branch_head(rule_extraction.rule_proposal_branch())
    monkeypatch.setattr(rule_extraction, "_llm_call", lambda **_kwargs: _rule_fixture())

    result = rule_extraction.propose_rules_for_paper(
        repo,
        source_paper=PAPER,
        model_name="test-model",
        dry_run=True,
    )

    assert result.commit_sha is None
    assert result.rule_ids == ("rule-001",)
    assert repo.snapshot.branch_head(rule_extraction.rule_proposal_branch()) == before

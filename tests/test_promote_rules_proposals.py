from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.app.rules import RuleWorkflowError, parse_atom
from propstore.families.documents.predicates import PredicateDocument, PredicatesFileDocument
from propstore.families.documents.rules import (
    RuleDocument,
    RuleExtractionProvenance,
    RuleProposalDocument,
)
from propstore.families.registry import PredicateFileRef, RuleFileRef
from propstore.families.registry import RuleProposalRef
from propstore.heuristic.rule_extraction import rule_proposal_branch
from propstore.proposals import UnknownProposalPath
from propstore.repository import Repository


PAPER = "Ioannidis_2005_WhyMostPublishedResearch"
_NAME = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)


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
                PredicateDocument(
                    id="low_trust",
                    arity=1,
                    arg_types=("paper_id",),
                    description="Low trust classification.",
                ),
                PredicateDocument(
                    id="high_trust",
                    arity=1,
                    arg_types=("paper_id",),
                    description="High trust classification.",
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


def _seed_direct_rule_proposal(
    repo: Repository,
    *,
    paper: str,
    rule_id: str,
    predicate_id: str,
) -> str:
    document = RuleProposalDocument(
        source_paper=paper,
        rule_id=rule_id,
        proposed_rule=RuleDocument(
            id=rule_id,
            kind="defeasible",
            head=parse_atom(f"{predicate_id}(P)"),
        ),
        predicates_referenced=(f"{predicate_id}/1",),
        extraction_provenance=RuleExtractionProvenance(
            operations=("test",),
            agent="test",
            model="test-model",
            prompt_sha="prompt",
            notes_sha="notes",
            predicates_sha="predicates",
            status="ok",
        ),
        extraction_date="2026-05-05T00:00:00Z",
    )
    with repo.families.transact(
        message=f"Record rule proposal {rule_id}",
        branch=rule_proposal_branch(),
    ) as transaction:
        transaction.proposal_rules.save(RuleProposalRef(paper, rule_id), document)
        transaction.transaction.commit()
        commit_sha = transaction.commit_sha
    assert commit_sha is not None
    return commit_sha


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


@pytest.mark.property
@given(paper=_NAME, rule_id=_NAME, predicate_id=_NAME)
@settings(deadline=None, max_examples=10)
def test_generated_rule_proposal_promotion_rejects_undeclared_predicates(
    paper: str,
    rule_id: str,
    predicate_id: str,
) -> None:
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        from propstore.proposals_rules import (
            plan_rule_proposal_promotion,
            promote_rule_proposals,
        )

        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        master_before = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
        _seed_direct_rule_proposal(
            repo,
            paper=paper,
            rule_id=rule_id,
            predicate_id=predicate_id,
        )

        plan = plan_rule_proposal_promotion(repo, source_paper=paper, rule_ids=(rule_id,))
        with pytest.raises(RuleWorkflowError, match="undeclared predicate"):
            promote_rule_proposals(repo, plan)

        assert repo.snapshot.branch_head(repo.snapshot.primary_branch_name()) == master_before
        assert repo.families.rules.load(RuleFileRef(f"{paper}/{rule_id}")) is None

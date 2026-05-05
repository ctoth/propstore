from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.app.predicates import PredicateWorkflowError
from propstore.families.documents.predicates import (
    PredicateDeclaration,
    PredicateDocument,
    PredicateExtractionProvenance,
    PredicateProposalDocument,
    PredicatesFileDocument,
)
from propstore.families.registry import PredicateFileRef, PredicateProposalRef
from propstore.heuristic.predicate_extraction import predicate_proposal_branch
from propstore.proposals import UnknownProposalPath
from propstore.repository import Repository


PAPER = "Ioannidis_2005_WhyMostPublishedResearch"
_NAME = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)


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


def _seed_direct_proposal(repo: Repository, *, paper: str, predicate_id: str) -> str:
    document = PredicateProposalDocument(
        source_paper=paper,
        proposed_declarations=(
            PredicateDeclaration(
                name=predicate_id,
                arity=1,
                arg_types=("paper_id",),
                description="Generated predicate.",
            ),
        ),
        extraction_provenance=PredicateExtractionProvenance(
            operations=("test",),
            agent="test",
            model="test-model",
            prompt_sha="prompt",
            notes_sha="notes",
            status="ok",
        ),
        extraction_date="2026-05-05T00:00:00Z",
    )
    with repo.families.transact(
        message=f"Record predicate proposals for {paper}",
        branch=predicate_proposal_branch(),
    ) as transaction:
        transaction.proposal_predicates.save(PredicateProposalRef(paper), document)
        transaction.transaction.commit()
        commit_sha = transaction.commit_sha
    assert commit_sha is not None
    return commit_sha


def _seed_canonical_predicate(repo: Repository, *, file_name: str, predicate_id: str) -> None:
    repo.families.predicates.save(
        PredicateFileRef(file_name),
        PredicatesFileDocument(
            predicates=(
                PredicateDocument(
                    id=predicate_id,
                    arity=1,
                    arg_types=("paper_id",),
                    description="Existing predicate.",
                ),
            )
        ),
        message=f"Seed {predicate_id}",
    )


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


@pytest.mark.property
@given(existing_file=_NAME, proposed_file=_NAME, predicate_id=_NAME)
@settings(deadline=None, max_examples=10)
def test_generated_predicate_proposal_promotion_rejects_global_duplicates(
    existing_file: str,
    proposed_file: str,
    predicate_id: str,
) -> None:
    if existing_file == proposed_file:
        proposed_file = f"{proposed_file}_other"
    tmp_dir = tempfile.TemporaryDirectory()
    with tmp_dir:
        from propstore.proposals_predicates import (
            plan_predicate_proposal_promotion,
            promote_predicate_proposals,
        )

        repo = Repository.init(Path(tmp_dir.name) / "knowledge")
        _seed_canonical_predicate(
            repo,
            file_name=existing_file,
            predicate_id=predicate_id,
        )
        master_before = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
        _seed_direct_proposal(repo, paper=proposed_file, predicate_id=predicate_id)

        plan = plan_predicate_proposal_promotion(repo, source_paper=proposed_file)
        with pytest.raises(PredicateWorkflowError, match="already declared"):
            promote_predicate_proposals(repo, plan)

        assert repo.snapshot.branch_head(repo.snapshot.primary_branch_name()) == master_before
        assert repo.families.predicates.load(PredicateFileRef(proposed_file)) is None

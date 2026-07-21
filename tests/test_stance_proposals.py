"""Phase 8-4: stance proposal artifacts + the promote workflow.

Ports the owner-layer behaviour of the reference stance-proposal suites
(test_proposal_promotion, test_promote_stance_proposals_idempotency,
test_plan_stance_proposal_promotion_typo_path) to the rewrite charters. Stance
proposals are recorded with :func:`commit_stance_proposal` (the NLI/LLM classifier
that produced them is the agent-workflow layer's concern); the CLI surface
(test_promote_cli_*) stays Phase 10.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from doxa import Opinion

from propstore.families.claims import Claim
from propstore.families.relations import StanceProposal, StanceProposalRef
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.proposal_promotion import UnknownProposalPath
from propstore.proposals import (
    commit_stance_proposal,
    plan_stance_proposal_promotion,
    promote_stance_proposals,
    stance_proposal_branch,
    stance_proposal_relpath,
)
from propstore.repository import Repository
from propstore.stances import StanceType


def _seed_claims(repo: Repository) -> None:
    for claim_id in ("claim_a", "claim_b"):
        repo.families.claim.save(
            claim_id, Claim(claim_id=claim_id), message=f"seed {claim_id}"
        )


def _record(repo: Repository) -> str:
    return commit_stance_proposal(
        repo,
        source_claim_id="claim_a",
        target_claim_id="claim_b",
        stance_type=StanceType.SUPPORTS,
        resolution_model="test-model",
        confidence=0.7,
        opinion=Opinion(0.7, 0.1, 0.2, 0.5),
        note="test proposal",
    )


# --- charter / paths -----------------------------------------------------------


def test_proposal_stances_family_is_registered(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    ref = StanceProposalRef("ps:stance:abc")
    assert repo.families.proposal_stances.family is (
        PROPSTORE_FAMILY_REGISTRY.by_name("proposal_stances").artifact_family
    )
    assert repo.families.proposal_stances.address(ref).require_path() == (
        "stances/ps__stance__abc.yaml"
    )


def test_stance_proposal_branch_and_relpath_are_fixed() -> None:
    assert stance_proposal_branch() == "proposal/stances"
    assert stance_proposal_relpath("ps:stance:abc") == "stances/ps__stance__abc.yaml"


# --- record / promote lifecycle ------------------------------------------------


def test_record_writes_only_to_proposal_branch(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_claims(repo)
    stance_id = _record(repo)

    # Nothing canonical was written by proposing.
    assert list(repo.families.stance.iter_refs()) == []
    proposal_tip = repo.require_git().branch_sha(stance_proposal_branch())
    assert proposal_tip is not None
    document = repo.families.proposal_stances.require(
        StanceProposalRef(stance_id), commit=proposal_tip
    )
    assert isinstance(document, StanceProposal)
    assert document.source_claim_id == "claim_a"
    assert document.opinion_uncertainty == pytest.approx(0.2)


def test_plan_selects_recorded_proposals(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_claims(repo)
    stance_id = _record(repo)

    plan = plan_stance_proposal_promotion(repo)
    assert plan.branch == stance_proposal_branch()
    assert plan.has_branch is True
    assert len(plan.items) == 1
    assert plan.items[0].stance_id == stance_id
    assert plan.items[0].source_claim == "claim_a"
    assert plan.items[0].filename == stance_proposal_relpath(stance_id).split("/")[-1]


def test_promote_writes_canonical_and_is_idempotent(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_claims(repo)
    stance_id = _record(repo)

    result = promote_stance_proposals(repo, plan_stance_proposal_promotion(repo))
    assert result.moved == 1

    stance = repo.families.stance.require(stance_id)
    assert stance.source_claim_id == "claim_a"
    assert stance.target_claim_id == "claim_b"
    assert stance.stance_type is StanceType.SUPPORTS
    opinion = stance.opinion()
    assert opinion is not None
    assert opinion.b == pytest.approx(0.7)

    # Re-promoting the same proposal yields the same canonical edge (idempotent).
    again = promote_stance_proposals(repo, plan_stance_proposal_promotion(repo))
    assert again.moved == 1
    assert repo.families.stance.require(stance_id).stance_type is StanceType.SUPPORTS


def test_plan_missing_branch_has_no_items(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    plan = plan_stance_proposal_promotion(repo)
    assert plan.has_branch is False
    assert plan.items == ()


def test_plan_unknown_stance_id_raises(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    _seed_claims(repo)
    stance_id = _record(repo)

    with pytest.raises(UnknownProposalPath) as excinfo:
        plan_stance_proposal_promotion(repo, stance_id="ps:stance:typo")

    assert excinfo.value.requested_path == "ps:stance:typo"
    assert excinfo.value.available == (
        stance_proposal_relpath(stance_id).split("/")[-1],
    )

"""Stance proposal recording and promotion (heuristic layer 3 → layer 1).

A stance proposal is a heuristic-layer candidate stance — what a classifier
proposed one claim's position toward another to be — recorded on the
``proposal/stances`` branch. :func:`commit_stance_proposal` records the candidate
(the classifier that produced it is the agent-workflow layer's concern; this only
durably stores what it proposed and never touches the canonical corpus).
:func:`plan_stance_proposal_promotion` and :func:`promote_stance_proposals` are
the explicit accept-then-promote path that writes the candidate as a canonical
:class:`~propstore.families.relations.Stance`. Because both the proposal and the
canonical edge are keyed by the same content-derived ``stance_id``, promoting the
same proposal twice is naturally idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from doxa import Opinion

from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.relations import (
    STANCE_PROPOSAL_BRANCH,
    Stance,
    StanceProposal,
    StanceProposalRef,
)
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    UnknownProposalPath,
    commit_planned_canonical_artifacts,
)
from propstore.stances import StanceType

if TYPE_CHECKING:
    from propstore.repository import Repository


def stance_proposal_branch() -> str:
    """Return the branch every stance proposal is recorded on."""

    branch = STANCE_PROPOSAL_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("stance proposal branch placement must be fixed")
    return branch


def stance_proposal_relpath(stance_id: str) -> str:
    """Return the repo-relative path a stance proposal is stored at.

    Derived from the family placement (``stances/<id>.yaml`` with the stance id's
    colons lowered to ``__``), so it stays in lock-step with storage and needs no
    fabricated repository owner.
    """

    return f"stances/{stance_id.replace(':', '__')}.yaml"


def stance_proposal_filename(stance_id: str) -> str:
    """Return just the filename a stance proposal is stored under."""

    return Path(stance_proposal_relpath(stance_id)).name


def commit_stance_proposal(
    repo: Repository,
    *,
    source_claim_id: str,
    target_claim_id: str,
    stance_type: StanceType,
    resolution_model: str | None = None,
    confidence: float | None = None,
    opinion: Opinion | None = None,
    note: str | None = None,
) -> str:
    """Record one stance proposal; return its content-derived ``stance_id``.

    Writes only to the proposal branch. The opinion is decomposed into its four
    Jøsang components when present and left absent (``None``) otherwise — honest
    ignorance, never a fabricated mass.
    """

    stance_id = derive_stance_artifact_id(
        source_claim_id=source_claim_id,
        target_claim_id=target_claim_id,
        stance_type=stance_type.value,
    )
    document = StanceProposal(
        stance_id=stance_id,
        source_claim_id=source_claim_id,
        target_claim_id=target_claim_id,
        stance_type=stance_type,
        resolution_model=resolution_model,
        confidence=confidence,
        opinion_belief=None if opinion is None else opinion.b,
        opinion_disbelief=None if opinion is None else opinion.d,
        opinion_uncertainty=None if opinion is None else opinion.u,
        opinion_base_rate=None if opinion is None else opinion.a,
        note=note,
    )
    bound = repo.families.transact(
        message=f"Record stance proposal {stance_id}",
        branch=stance_proposal_branch(),
    )
    with bound as transaction:
        transaction.proposal_stances.save(StanceProposalRef(stance_id), document)
    return stance_id


@dataclass(frozen=True)
class StanceProposalPromotionItem:
    stance_id: str
    source_claim: str
    filename: str


@dataclass(frozen=True)
class StanceProposalPromotionPlan:
    branch: str
    proposal_tip: str | None
    items: tuple[StanceProposalPromotionItem, ...]

    @property
    def has_branch(self) -> bool:
        return self.proposal_tip is not None


@dataclass(frozen=True)
class StanceProposalPromotionResult:
    moved: int
    branch: str
    promoted_items: tuple[StanceProposalPromotionItem, ...]


def plan_stance_proposal_promotion(
    repo: Repository, *, stance_id: str | None = None
) -> StanceProposalPromotionPlan:
    """Plan the canonical stance writes a promotion would perform.

    With no ``stance_id`` every recorded proposal is selected (sorted by id); with
    one, only that proposal — raising :class:`UnknownProposalPath` if it is not on
    the branch.
    """

    branch = stance_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(branch)
    if proposal_tip is None:
        return StanceProposalPromotionPlan(branch=branch, proposal_tip=None, items=())

    available = {
        ref.stance_id
        for ref in repo.families.proposal_stances.iter_refs(
            branch=branch, commit=proposal_tip
        )
    }
    if stance_id is not None:
        if stance_id not in available:
            raise UnknownProposalPath(
                stance_id,
                tuple(sorted(stance_proposal_filename(known) for known in available)),
            )
        selected = [stance_id]
    else:
        selected = sorted(available)

    items: list[StanceProposalPromotionItem] = []
    for selected_id in selected:
        proposal = _load_proposal(repo, selected_id, proposal_tip)
        items.append(
            StanceProposalPromotionItem(
                stance_id=selected_id,
                source_claim=proposal.source_claim_id or "",
                filename=stance_proposal_filename(selected_id),
            )
        )
    return StanceProposalPromotionPlan(
        branch=branch, proposal_tip=proposal_tip, items=tuple(items)
    )


def _load_proposal(
    repo: Repository, stance_id: str, proposal_tip: str
) -> StanceProposal:
    proposal = repo.families.proposal_stances.require(
        StanceProposalRef(stance_id), commit=proposal_tip
    )
    if not isinstance(proposal, StanceProposal):  # pragma: no cover - typing
        raise TypeError(f"proposal {stance_id!r} is not a StanceProposal")
    return proposal


def promote_stance_proposals(
    repo: Repository, plan: StanceProposalPromotionPlan
) -> StanceProposalPromotionResult:
    """Promote the planned stance proposals into canonical stances."""

    if not plan.items:
        return StanceProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("stance proposal promotion requires a proposal tip")

    artifacts: list[PlannedCanonicalArtifact[str, Stance]] = []
    for item in plan.items:
        proposal = _load_proposal(repo, item.stance_id, plan.proposal_tip)
        artifacts.append(
            PlannedCanonicalArtifact(
                proposal.stance_id,
                Stance(
                    stance_id=proposal.stance_id,
                    source_claim_id=proposal.source_claim_id,
                    target_claim_id=proposal.target_claim_id,
                    stance_type=proposal.stance_type,
                    resolution_model=proposal.resolution_model,
                    confidence=proposal.confidence,
                    opinion_belief=proposal.opinion_belief,
                    opinion_disbelief=proposal.opinion_disbelief,
                    opinion_uncertainty=proposal.opinion_uncertainty,
                    opinion_base_rate=proposal.opinion_base_rate,
                ),
            )
        )

    moved = commit_planned_canonical_artifacts(
        repo.families.transact,
        message=f"Promote {len(artifacts)} stance proposal(s) from {plan.branch}",
        family=lambda transaction: transaction.stance,
        artifacts=artifacts,
    )
    return StanceProposalPromotionResult(moved, plan.branch, plan.items)

"""Predicate proposal recording and promotion (heuristic layer 3 → layer 1).

A predicate proposal is a paper's candidate predicate vocabulary, recorded on the
``proposal/predicates`` branch. :func:`propose_predicates` records a candidate
batch (the heuristic/LLM that *produced* the declarations is the agent-workflow
layer's concern — this module only durably stores what it proposed and never
touches the canonical corpus). :func:`plan_predicate_proposal_promotion` and
:func:`promote_predicate_proposals` are the explicit, accept-then-promote path
that turns an already-recorded proposal into canonical :class:`Predicate`
artifacts, atomically and idempotently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.families.predicates import (
    PREDICATE_PROPOSAL_BRANCH,
    Predicate,
    PredicateDeclaration,
    PredicateExtractionProvenance,
    PredicateProposal,
    PredicateProposalRef,
)
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    UnknownProposalPath,
    commit_planned_canonical_artifacts,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


class PredicateProposalConflict(ValueError):
    """A proposed predicate name is already canonically declared by another group."""

    def __init__(self, predicate_id: str, existing_group: str | None) -> None:
        self.predicate_id = predicate_id
        self.existing_group = existing_group
        super().__init__(
            f"predicate {predicate_id!r} is already declared"
            + (f" by {existing_group!r}" if existing_group else "")
        )


def predicate_proposal_branch() -> str:
    """Return the branch every predicate proposal is recorded on."""

    branch = PREDICATE_PROPOSAL_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("predicate proposal branch placement must be fixed")
    return branch


def propose_predicates(
    repo: Repository,
    *,
    source_paper: str,
    declarations: tuple[PredicateDeclaration, ...],
    extraction_provenance: PredicateExtractionProvenance,
    extraction_date: str,
) -> str | None:
    """Record a predicate proposal batch for *source_paper*; return the commit sha.

    Writes only to the proposal branch — the canonical corpus is untouched. An
    empty declaration batch records nothing and returns ``None``.
    """

    if not declarations:
        return None
    document = PredicateProposal(
        source_paper=source_paper,
        proposed_declarations=declarations,
        extraction_provenance=extraction_provenance,
        extraction_date=extraction_date,
    )
    bound = repo.families.transact(
        message=f"Record predicate proposals for {source_paper}",
        branch=predicate_proposal_branch(),
    )
    with bound as transaction:
        transaction.proposal_predicates.save(
            PredicateProposalRef(source_paper), document
        )
    return bound.commit_sha


@dataclass(frozen=True)
class PredicateProposalPromotionItem:
    """One canonical predicate a promotion will write from a proposal."""

    source_paper: str
    predicate_id: str


@dataclass(frozen=True)
class PredicateProposalPromotionPlan:
    """The eligible predicate writes for one paper's proposal, at a proposal tip."""

    branch: str
    proposal_tip: str | None
    items: tuple[PredicateProposalPromotionItem, ...]

    @property
    def has_branch(self) -> bool:
        return self.proposal_tip is not None


@dataclass(frozen=True)
class PredicateProposalPromotionResult:
    moved: int
    branch: str
    promoted_items: tuple[PredicateProposalPromotionItem, ...]


def _load_proposal(
    repo: Repository, *, source_paper: str, proposal_tip: str
) -> PredicateProposal:
    proposal = repo.families.proposal_predicates.require(
        PredicateProposalRef(source_paper), commit=proposal_tip
    )
    if not isinstance(proposal, PredicateProposal):  # pragma: no cover - typing
        raise TypeError(f"proposal {source_paper!r} is not a PredicateProposal")
    return proposal


def plan_predicate_proposal_promotion(
    repo: Repository, *, source_paper: str
) -> PredicateProposalPromotionPlan:
    """Plan the canonical predicate writes a promotion of *source_paper* would do.

    Declarations already promoted from the current proposal tip are skipped, so a
    re-plan after a completed promotion yields no items (idempotent). Raises
    :class:`UnknownProposalPath` when the paper has no proposal on the branch.
    """

    branch = predicate_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(branch)
    if proposal_tip is None:
        return PredicateProposalPromotionPlan(branch=branch, proposal_tip=None, items=())

    available = tuple(
        ref.source_paper
        for ref in repo.families.proposal_predicates.iter_refs(
            branch=branch, commit=proposal_tip
        )
    )
    if source_paper not in available:
        raise UnknownProposalPath(source_paper, tuple(sorted(available)))

    proposal = _load_proposal(
        repo, source_paper=source_paper, proposal_tip=proposal_tip
    )
    items: list[PredicateProposalPromotionItem] = []
    for declaration in proposal.proposed_declarations:
        existing = repo.families.predicate.load(_canonical_ref(declaration.name))
        if existing is not None and existing.promoted_from_sha == proposal_tip:
            continue
        items.append(
            PredicateProposalPromotionItem(
                source_paper=source_paper, predicate_id=declaration.name
            )
        )
    return PredicateProposalPromotionPlan(
        branch=branch, proposal_tip=proposal_tip, items=tuple(items)
    )


def _canonical_ref(predicate_id: str) -> str:
    # Canonical predicates are keyed by their id (FlatYamlPlacement over ``str``).
    return predicate_id


def promote_predicate_proposals(
    repo: Repository, plan: PredicateProposalPromotionPlan
) -> PredicateProposalPromotionResult:
    """Promote the planned predicate declarations into canonical artifacts.

    Every declaration that names an existing canonical predicate authored by a
    *different* group is a conflict: the promotion raises before any write, so the
    canonical corpus is left exactly as it was (rivals are never silently merged).
    """

    if not plan.items:
        return PredicateProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("predicate proposal promotion requires a proposal tip")

    artifacts: list[PlannedCanonicalArtifact[str, Predicate]] = []
    for item in plan.items:
        proposal = _load_proposal(
            repo, source_paper=item.source_paper, proposal_tip=plan.proposal_tip
        )
        declaration = _declaration_by_name(proposal, item.predicate_id)
        existing = repo.families.predicate.load(_canonical_ref(item.predicate_id))
        if existing is not None and existing.authoring_group not in (
            None,
            item.source_paper,
        ):
            raise PredicateProposalConflict(
                item.predicate_id, existing.authoring_group
            )
        artifacts.append(
            PlannedCanonicalArtifact(
                _canonical_ref(item.predicate_id),
                Predicate(
                    predicate_id=declaration.name,
                    arity=declaration.arity,
                    arg_types=declaration.arg_types,
                    description=declaration.description,
                    authoring_group=item.source_paper,
                    promoted_from_sha=plan.proposal_tip,
                ),
            )
        )

    moved = commit_planned_canonical_artifacts(
        repo.families.transact,
        message=f"Promote {len(artifacts)} predicate proposal(s) from {plan.branch}",
        family=lambda transaction: transaction.predicate,
        artifacts=artifacts,
    )
    return PredicateProposalPromotionResult(moved, plan.branch, plan.items)


def _declaration_by_name(
    proposal: PredicateProposal, name: str
) -> PredicateDeclaration:
    for declaration in proposal.proposed_declarations:
        if declaration.name == name:
            return declaration
    raise KeyError(name)

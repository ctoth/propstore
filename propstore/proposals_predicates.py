"""Predicate proposal planning and promotion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.families.documents.predicates import (
    PredicateDocument,
    PredicatesFileDocument,
)
from propstore.families.registry import (
    PredicateFileRef,
    PredicateProposalRef,
)
from propstore.proposals import UnknownProposalPath

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class PredicateProposalPromotionItem:
    source_paper: str
    source_relpath: str
    target_path: Path
    filename: str


@dataclass(frozen=True)
class PredicateProposalPromotionPlan:
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


def _proposal_branch(repo: "Repository") -> str:
    from propstore.heuristic.predicate_extraction import predicate_proposal_branch

    return predicate_proposal_branch()


def plan_predicate_proposal_promotion(
    repo: "Repository",
    *,
    source_paper: str,
) -> PredicateProposalPromotionPlan:
    proposal_branch = _proposal_branch(repo)
    proposal_tip = repo.snapshot.branch_head(proposal_branch)
    if proposal_tip is None:
        return PredicateProposalPromotionPlan(proposal_branch, None, ())

    available = tuple(
        repo.families.proposal_predicates.iter(
            branch=proposal_branch,
            commit=proposal_tip,
        )
    )
    available_by_paper = {ref.source_paper: ref for ref in available}
    ref = available_by_paper.get(source_paper)
    if ref is None:
        raise UnknownProposalPath(source_paper, tuple(sorted(available_by_paper)))

    canonical_ref = PredicateFileRef(source_paper)
    existing = repo.families.predicates.load(canonical_ref)
    if existing is not None and existing.promoted_from_sha == proposal_tip:
        return PredicateProposalPromotionPlan(proposal_branch, proposal_tip, ())

    proposal_path = repo.families.proposal_predicates.address(ref).require_path()
    target_path = repo.root / repo.families.predicates.address(canonical_ref).require_path()
    return PredicateProposalPromotionPlan(
        branch=proposal_branch,
        proposal_tip=proposal_tip,
        items=(
            PredicateProposalPromotionItem(
                source_paper=source_paper,
                source_relpath=f"{proposal_branch}:{proposal_path}",
                target_path=target_path,
                filename="declarations.yaml",
            ),
        ),
    )


def promote_predicate_proposals(
    repo: "Repository",
    plan: PredicateProposalPromotionPlan,
) -> PredicateProposalPromotionResult:
    if not plan.items:
        return PredicateProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("predicate proposal promotion requires a proposal tip")

    with repo.families.transact(
        message=f"Promote {len(plan.items)} predicate proposal file(s) from {plan.branch}",
    ) as transaction:
        for item in plan.items:
            proposal_ref = PredicateProposalRef(item.source_paper)
            proposal = repo.families.proposal_predicates.require(
                proposal_ref,
                commit=plan.proposal_tip,
            )
            canonical_ref = PredicateFileRef(item.source_paper)
            document = PredicatesFileDocument(
                predicates=tuple(
                    PredicateDocument(
                        id=declaration.name,
                        arity=declaration.arity,
                        arg_types=tuple(str(arg_type) for arg_type in declaration.arg_types),
                        description=declaration.description,
                    )
                    for declaration in proposal.proposed_declarations
                ),
                promoted_from_sha=plan.proposal_tip,
            )
            transaction.predicates.save(canonical_ref, document)
    return PredicateProposalPromotionResult(len(plan.items), plan.branch, plan.items)

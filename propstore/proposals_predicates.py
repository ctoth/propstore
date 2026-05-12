"""Predicate proposal planning and promotion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.families.documents.predicates import (
    PredicateDocument,
)
from propstore.families.registry import (
    PredicateProposalRef,
    PredicateRef,
)
from propstore.proposals import UnknownProposalPath
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    commit_planned_canonical_artifacts,
)
from propstore.app.predicates import (
    _PREDICATE_MUTATION_LOCK,
    reject_predicate_document_conflicts,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class PredicateProposalPromotionItem:
    source_paper: str
    predicate_id: str
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

    proposal = repo.families.proposal_predicates.require(ref, commit=proposal_tip)
    proposed_declarations = tuple(proposal.proposed_declarations)
    existing = tuple(
        repo.families.predicates.load(PredicateRef(declaration.name))
        for declaration in proposed_declarations
    )
    if proposed_declarations and all(
        document is not None and document.promoted_from_sha == proposal_tip
        for document in existing
    ):
        return PredicateProposalPromotionPlan(proposal_branch, proposal_tip, ())

    proposal_path = repo.families.proposal_predicates.address(ref).require_path()
    return PredicateProposalPromotionPlan(
        branch=proposal_branch,
        proposal_tip=proposal_tip,
        items=tuple(
            PredicateProposalPromotionItem(
                source_paper=source_paper,
                predicate_id=declaration.name,
                source_relpath=f"{proposal_branch}:{proposal_path}",
                target_path=repo.root
                / repo.families.predicates.address(PredicateRef(declaration.name)).require_path(),
                filename=f"{declaration.name}.yaml",
            )
            for declaration in proposed_declarations
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

    artifacts: list[PlannedCanonicalArtifact[PredicateRef, PredicateDocument]] = []
    for item in plan.items:
        proposal_ref = PredicateProposalRef(item.source_paper)
        proposal = repo.families.proposal_predicates.require(
            proposal_ref,
            commit=plan.proposal_tip,
        )
        declarations = {
            declaration.name: declaration
            for declaration in proposal.proposed_declarations
        }
        declaration = declarations[item.predicate_id]
        canonical_ref = PredicateRef(item.predicate_id)
        artifacts.append(
            PlannedCanonicalArtifact(
                canonical_ref,
                PredicateDocument(
                    id=declaration.name,
                    arity=declaration.arity,
                    arg_types=tuple(str(arg_type) for arg_type in declaration.arg_types),
                    description=declaration.description,
                    authoring_group=item.source_paper,
                    promoted_from_sha=plan.proposal_tip,
                ),
            )
        )

    with _PREDICATE_MUTATION_LOCK, repo.head_bound_transaction(
        repo.snapshot.primary_branch_name(),
        path="proposal.predicates.promote",
    ) as head_txn:
        for artifact in artifacts:
            reject_predicate_document_conflicts(
                repo,
                commit=head_txn.expected_head,
                target_ref=artifact.ref,
                document=artifact.document,
            )

        commit_planned_canonical_artifacts(
            head_txn.families_transact,
            message=f"Promote {len(plan.items)} predicate proposal(s) from {plan.branch}",
            family=lambda transaction: transaction.predicates,
            artifacts=artifacts,
        )
    return PredicateProposalPromotionResult(len(plan.items), plan.branch, plan.items)

"""Rule proposal planning and selective promotion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.families.documents.rules import RuleDocument, RuleSourceDocument
from propstore.families.registry import RuleProposalRef, RuleRef
from propstore.proposals import UnknownProposalPath
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    commit_planned_canonical_artifacts,
)
from propstore.app.rules import _RULE_MUTATION_LOCK, reject_rule_document_conflicts

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class RuleProposalPromotionItem:
    source_paper: str
    rule_id: str
    source_relpath: str
    target_path: Path
    filename: str


@dataclass(frozen=True)
class RuleProposalPromotionPlan:
    branch: str
    proposal_tip: str | None
    items: tuple[RuleProposalPromotionItem, ...]

    @property
    def has_branch(self) -> bool:
        return self.proposal_tip is not None


@dataclass(frozen=True)
class RuleProposalPromotionResult:
    moved: int
    branch: str
    promoted_items: tuple[RuleProposalPromotionItem, ...]


def _proposal_branch() -> str:
    from propstore.heuristic.rule_extraction import rule_proposal_branch

    return rule_proposal_branch()


def _canonical_ref(_source_paper: str, rule_id: str) -> RuleRef:
    return RuleRef(rule_id)


def plan_rule_proposal_promotion(
    repo: "Repository",
    *,
    source_paper: str | None = None,
    rule_ids: tuple[str, ...] | None = None,
) -> RuleProposalPromotionPlan:
    proposal_branch = _proposal_branch()
    proposal_tip = repo.snapshot.branch_head(proposal_branch)
    if proposal_tip is None:
        return RuleProposalPromotionPlan(proposal_branch, None, ())

    available = tuple(
        repo.families.proposal_rules.iter(
            branch=proposal_branch,
            commit=proposal_tip,
        )
    )
    if source_paper is not None:
        available = tuple(ref for ref in available if ref.source_paper == source_paper)
    available_by_key = {(ref.source_paper, ref.rule_id): ref for ref in available}
    requested_keys = (
        tuple(available_by_key)
        if rule_ids is None
        else tuple((source_paper or "", rule_id) for rule_id in rule_ids)
    )

    missing = [
        rule_id
        for paper, rule_id in requested_keys
        if (paper, rule_id) not in available_by_key
    ]
    if missing:
        raise UnknownProposalPath(
            ", ".join(missing),
            tuple(sorted(rule_id for _paper, rule_id in available_by_key)),
        )

    items: list[RuleProposalPromotionItem] = []
    for key in requested_keys:
        ref = available_by_key[key]
        canonical_ref = _canonical_ref(ref.source_paper, ref.rule_id)
        existing = repo.families.rules.load(canonical_ref)
        if existing is not None and existing.promoted_from_sha == proposal_tip:
            continue
        proposal_path = repo.families.proposal_rules.address(ref).require_path()
        items.append(
            RuleProposalPromotionItem(
                source_paper=ref.source_paper,
                rule_id=ref.rule_id,
                source_relpath=f"{proposal_branch}:{proposal_path}",
                target_path=repo.root / repo.families.rules.address(canonical_ref).require_path(),
                filename=f"{ref.rule_id}.yaml",
            )
        )
    return RuleProposalPromotionPlan(proposal_branch, proposal_tip, tuple(items))


def promote_rule_proposals(
    repo: "Repository",
    plan: RuleProposalPromotionPlan,
) -> RuleProposalPromotionResult:
    if not plan.items:
        return RuleProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("rule proposal promotion requires a proposal tip")

    artifacts: list[PlannedCanonicalArtifact[RuleRef, RuleDocument]] = []
    for item in plan.items:
        proposal_ref = RuleProposalRef(item.source_paper, item.rule_id)
        proposal = repo.families.proposal_rules.require(
            proposal_ref,
            commit=plan.proposal_tip,
        )
        canonical_ref = _canonical_ref(item.source_paper, item.rule_id)
        proposed = proposal.proposed_rule
        artifacts.append(
            PlannedCanonicalArtifact(
                canonical_ref,
                RuleDocument(
                    id=proposed.id,
                    kind=proposed.kind,
                    head=proposed.head,
                    body=proposed.body,
                    source=RuleSourceDocument(paper=item.source_paper),
                    authoring_group=item.source_paper,
                    promoted_from_sha=plan.proposal_tip,
                ),
            )
        )

    git = repo.git
    if git is None:
        raise ValueError("rule proposal promotion requires a git-backed repository")
    with _RULE_MUTATION_LOCK, git.head_bound_transaction(
        repo.snapshot.primary_branch_name(),
    ) as head_txn:
        for artifact in artifacts:
            reject_rule_document_conflicts(
                repo,
                commit=head_txn.expected_head,
                target_ref=artifact.ref,
                document=artifact.document,
            )

        commit_planned_canonical_artifacts(
            lambda **kwargs: head_txn.families_transact(repo.families, **kwargs),
            message=f"Promote {len(plan.items)} rule proposal(s) from {plan.branch}",
            family=lambda transaction: transaction.rules,
            artifacts=artifacts,
        )
    return RuleProposalPromotionResult(len(plan.items), plan.branch, plan.items)

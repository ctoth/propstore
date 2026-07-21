"""Rule proposal promotion (heuristic layer 3 → layer 1).

A rule proposal is a heuristic-layer candidate DeLP rule recorded on the
``proposal/rules`` branch (one ``rules/<source_paper>/<rule_id>.yaml`` per rule).
:mod:`propstore.heuristic.rule_extraction` records them; this module is the
explicit accept-then-promote path that turns an already-recorded proposal into a
canonical :class:`~propstore.families.rules.DefeasibleRule`.

A promotion refuses to write a rule that references a predicate not declared in
the canonical corpus (:class:`RuleWorkflowError`): the rule would be unsatisfiable
at grounding time, so it is rejected before any write rather than silently
admitted. Because the canonical rule is keyed by ``rule_id`` and records the
``promoted_from_sha`` it came from, re-planning after a completed promotion yields
no items (idempotent).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.families.rules import (
    DefeasibleRule,
    RuleProposal,
    RuleProposalRef,
    rule_proposal_branch,
)
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    UnknownProposalPath,
    commit_planned_canonical_artifacts,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


class RuleWorkflowError(ValueError):
    """A rule proposal cannot be promoted (e.g. it references an undeclared predicate)."""


def _predicate_id(reference: str) -> str:
    """Return the predicate id portion of an ``id/arity`` reference."""

    return reference.split("/", 1)[0]


@dataclass(frozen=True)
class RuleProposalPromotionItem:
    """One canonical rule a promotion will write from a proposal."""

    source_paper: str
    rule_id: str


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


def _load_proposal(
    repo: Repository, *, source_paper: str, rule_id: str, proposal_tip: str
) -> RuleProposal:
    proposal = repo.families.proposal_rules.require(
        RuleProposalRef(source_paper, rule_id), commit=proposal_tip
    )
    if not isinstance(proposal, RuleProposal):  # pragma: no cover - typing
        raise TypeError(f"proposal {rule_id!r} is not a RuleProposal")
    return proposal


def plan_rule_proposal_promotion(
    repo: Repository, *, source_paper: str, rule_ids: tuple[str, ...]
) -> RuleProposalPromotionPlan:
    """Plan the canonical rule writes a promotion of *source_paper* would do.

    Each requested ``rule_id`` must be a recorded proposal for *source_paper* —
    an unknown id raises :class:`UnknownProposalPath`. Rules already promoted from
    the current proposal tip are skipped, so a re-plan after a completed promotion
    yields no items.
    """

    branch = rule_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(branch)
    if proposal_tip is None:
        return RuleProposalPromotionPlan(branch=branch, proposal_tip=None, items=())

    available = {
        (ref.source_paper, ref.rule_id)
        for ref in repo.families.proposal_rules.iter_refs(
            branch=branch, commit=proposal_tip
        )
    }
    items: list[RuleProposalPromotionItem] = []
    for rule_id in rule_ids:
        if (source_paper, rule_id) not in available:
            raise UnknownProposalPath(
                rule_id,
                tuple(sorted(f"{paper}/{rid}" for paper, rid in available)),
            )
        existing = repo.families.defeasible_rule.load(rule_id)
        if existing is not None and existing.promoted_from_sha == proposal_tip:
            continue
        items.append(
            RuleProposalPromotionItem(source_paper=source_paper, rule_id=rule_id)
        )
    return RuleProposalPromotionPlan(
        branch=branch, proposal_tip=proposal_tip, items=tuple(items)
    )


def promote_rule_proposals(
    repo: Repository, plan: RuleProposalPromotionPlan
) -> RuleProposalPromotionResult:
    """Promote the planned rule proposals into canonical defeasible rules.

    Every referenced predicate must already be declared canonically; an undeclared
    reference raises :class:`RuleWorkflowError` before any write, leaving the
    canonical corpus untouched (rivals are never silently admitted).
    """

    if not plan.items:
        return RuleProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("rule proposal promotion requires a proposal tip")

    artifacts: list[PlannedCanonicalArtifact[str, DefeasibleRule]] = []
    for item in plan.items:
        proposal = _load_proposal(
            repo,
            source_paper=item.source_paper,
            rule_id=item.rule_id,
            proposal_tip=plan.proposal_tip,
        )
        if proposal.proposed_rule is None:
            raise RuleWorkflowError(
                f"rule proposal {item.rule_id!r} carries no proposed rule"
            )
        for reference in proposal.predicates_referenced:
            if repo.families.predicate.load(_predicate_id(reference)) is None:
                raise RuleWorkflowError(
                    f"rule {item.rule_id!r} references undeclared predicate {reference!r}"
                )
        rule = proposal.proposed_rule
        artifacts.append(
            PlannedCanonicalArtifact(
                item.rule_id,
                DefeasibleRule(
                    rule_id=rule.id,
                    kind=rule.kind,
                    head=rule.head,
                    body=rule.body,
                    source=item.source_paper,
                    authoring_group=item.source_paper,
                    promoted_from_sha=plan.proposal_tip,
                ),
            )
        )

    moved = commit_planned_canonical_artifacts(
        repo.families.transact,
        message=f"Promote {len(artifacts)} rule proposal(s) from {plan.branch}",
        family=lambda transaction: transaction.defeasible_rule,
        artifacts=artifacts,
    )
    return RuleProposalPromotionResult(moved, plan.branch, plan.items)

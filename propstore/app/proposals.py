"""Application-layer proposal promotion workflows."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.proposals import StanceProposalPromotionPlan
from propstore.repository import Repository


@dataclass(frozen=True)
class ProposalPromotionRequest:
    path: str | None = None


@dataclass(frozen=True)
class ProposalPromotionItem:
    source_relpath: str
    target_path: str
    filename: str


@dataclass(frozen=True)
class ProposalPromotionPlanReport:
    branch: str
    has_branch: bool
    items: tuple[ProposalPromotionItem, ...]
    plan: StanceProposalPromotionPlan


@dataclass(frozen=True)
class ProposalPromotionResult:
    moved: int


def plan_proposal_promotion(
    repo: Repository,
    request: ProposalPromotionRequest,
) -> ProposalPromotionPlanReport:
    from propstore.proposals import plan_stance_proposal_promotion

    plan = plan_stance_proposal_promotion(repo, path=request.path)
    return ProposalPromotionPlanReport(
        branch=plan.branch,
        has_branch=plan.has_branch,
        items=tuple(
            ProposalPromotionItem(
                source_relpath=item.source_relpath,
                target_path=str(item.target_path),
                filename=item.filename,
            )
            for item in plan.items
        ),
        plan=plan,
    )


def promote_proposals(
    repo: Repository,
    plan_report: ProposalPromotionPlanReport,
) -> ProposalPromotionResult:
    from propstore.proposals import promote_stance_proposals

    result = promote_stance_proposals(repo, plan_report.plan)
    return ProposalPromotionResult(moved=result.moved)

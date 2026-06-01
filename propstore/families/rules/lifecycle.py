from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from quire.lifecycle import (
    FamilyRecordWrite,
    LifecycleCallbacks,
    TransitionContext,
    TransitionPlan,
    run_transition_batch,
)

from propstore.app.rules import _RULE_MUTATION_LOCK, reject_rule_document_conflicts
from propstore.families.registry import RuleProposalRef, RuleRef
from propstore.families.rules.declaration import (
    AUTHORED_RULE_PROPOSAL_CHARTER,
    AuthoredRuleProposalArtifact,
    RuleDocument,
    RuleSourceDocument,
)
from propstore.proposal_lifecycle import (
    ProposalPromotionItem,
    ProposalPromotionPlan,
    ProposalPromotionResult,
    UnknownProposalPath,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


def rule_proposal_branch() -> str:
    from propstore.heuristic.rule_extraction import rule_proposal_branch

    return rule_proposal_branch()


def _canonical_ref(_source_paper: str, rule_id: str) -> RuleRef:
    return RuleRef(rule_id)


def plan_rule_proposal_promotion(
    repo: "Repository",
    *,
    source_paper: str | None = None,
    rule_ids: tuple[str, ...] | None = None,
) -> ProposalPromotionPlan[RuleProposalRef]:
    proposal_branch = rule_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(proposal_branch)
    if proposal_tip is None:
        return ProposalPromotionPlan(proposal_branch, None, ())

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

    items: list[ProposalPromotionItem[RuleProposalRef]] = []
    for key in requested_keys:
        ref = available_by_key[key]
        canonical_ref = _canonical_ref(ref.source_paper, ref.rule_id)
        existing = repo.families.rules.load(canonical_ref)
        if existing is not None and existing.promoted_from_sha == proposal_tip:
            continue
        proposal_path = repo.families.proposal_rules.address(ref).require_path()
        items.append(
            ProposalPromotionItem(
                ref=ref,
                artifact_id=ref.rule_id,
                source_paper=ref.source_paper,
                rule_id=ref.rule_id,
                source_relpath=f"{proposal_branch}:{proposal_path}",
                target_path=repo.root
                / repo.families.rules.address(canonical_ref).require_path(),
                filename=f"{ref.rule_id}.yaml",
            )
        )
    return ProposalPromotionPlan(proposal_branch, proposal_tip, tuple(items))


def apply_rule_proposal_promotion(
    repo: "Repository",
    plan: ProposalPromotionPlan[RuleProposalRef],
) -> ProposalPromotionResult[RuleProposalRef]:
    if not plan.items:
        return ProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("rule proposal promotion requires a proposal tip")

    proposal_documents = tuple(
        repo.families.proposal_rules.require(
            item.ref,
            commit=plan.proposal_tip,
        )
        for item in plan.items
    )
    batch_result = run_transition_batch(
        charter=AUTHORED_RULE_PROPOSAL_CHARTER,
        transition="promote_proposal",
        records=proposal_documents,
        context=TransitionContext(metadata={"proposal_tip": plan.proposal_tip}),
        callbacks=LifecycleCallbacks(
            materializers={
                "rule_proposal_to_canonical": _materialize_rule_proposal,
            },
        ),
    )
    writes = tuple(
        write for item_result in batch_result.items for write in item_result.plan.writes
    )

    git = repo.git
    if git is None:
        raise ValueError("rule proposal promotion requires a git-backed repository")
    with (
        _RULE_MUTATION_LOCK,
        git.head_bound_transaction(
            repo.require_git().primary_branch_name(),
        ) as head_txn,
    ):
        for write in writes:
            reject_rule_document_conflicts(
                repo,
                commit=head_txn.expected_head,
                target_ref=RuleRef(write.identity),
                document=cast(RuleDocument, write.record),
            )

        if writes:
            with head_txn.families_transact(
                repo.families,
                message=f"Promote {len(plan.items)} rule proposal(s) from {plan.branch}",
            ) as transaction:
                for write in writes:
                    _save_rule_promotion_write(transaction, write)
    return ProposalPromotionResult(len(plan.items), plan.branch, plan.items)


def _materialize_rule_proposal(
    record: object,
    context: TransitionContext,
) -> TransitionPlan:
    proposal_tip = context.metadata.get("proposal_tip")
    if not isinstance(proposal_tip, str) or not proposal_tip:
        raise ValueError("rule proposal transition requires proposal_tip metadata")
    proposal = cast(AuthoredRuleProposalArtifact, record)
    proposed = proposal.proposed_rule
    document = RuleDocument(
        id=proposed.id,
        kind=proposed.kind,
        head=proposed.head,
        body=proposed.body,
        source=RuleSourceDocument(paper=proposal.source_paper),
        authoring_group=proposal.source_paper,
        promoted_from_sha=proposal_tip,
    )
    return TransitionPlan(
        writes=(
            FamilyRecordWrite(
                family="rules",
                identity=proposal.rule_id,
                state="canonical",
                record=document,
            ),
        )
    )


def _save_rule_promotion_write(transaction: Any, write: FamilyRecordWrite) -> None:
    if write.family != "rules":
        raise ValueError(f"unknown rule proposal write family: {write.family!r}")
    transaction.rules.save(
        RuleRef(write.identity),
        cast(RuleDocument, write.record),
    )

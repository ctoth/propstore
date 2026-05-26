from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from quire.lifecycle import (
    FamilyRecordWrite,
    LifecycleCallbacks,
    TransitionContext,
    TransitionPlan,
    run_transition_batch,
)

from propstore.app.predicates import (
    _PREDICATE_MUTATION_LOCK,
    reject_predicate_document_conflicts,
)
from propstore.families.predicates.declaration import (
    PREDICATE_PROPOSAL_CHARTER,
    PredicateDeclaration,
    PredicateDocument,
)
from propstore.families.registry import PredicateProposalRef, PredicateRef
from propstore.proposal_lifecycle import (
    ProposalPromotionItem,
    ProposalPromotionPlan,
    ProposalPromotionResult,
    UnknownProposalPath,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class PredicateProposalTransitionRecord:
    name: str
    source_paper: str
    declaration: PredicateDeclaration


def predicate_proposal_branch() -> str:
    from propstore.heuristic.predicate_extraction import predicate_proposal_branch

    return predicate_proposal_branch()


def plan_predicate_proposal_promotion(
    repo: "Repository",
    *,
    source_paper: str,
) -> ProposalPromotionPlan[PredicateProposalRef]:
    proposal_branch = predicate_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(proposal_branch)
    if proposal_tip is None:
        return ProposalPromotionPlan(proposal_branch, None, ())

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
        return ProposalPromotionPlan(proposal_branch, proposal_tip, ())

    proposal_path = repo.families.proposal_predicates.address(ref).require_path()
    return ProposalPromotionPlan(
        branch=proposal_branch,
        proposal_tip=proposal_tip,
        items=tuple(
            ProposalPromotionItem(
                ref=ref,
                artifact_id=declaration.name,
                source_paper=source_paper,
                predicate_id=declaration.name,
                source_relpath=f"{proposal_branch}:{proposal_path}",
                target_path=repo.root
                / repo.families.predicates.address(
                    PredicateRef(declaration.name),
                ).require_path(),
                filename=f"{declaration.name}.yaml",
            )
            for declaration in proposed_declarations
        ),
    )


def apply_predicate_proposal_promotion(
    repo: "Repository",
    plan: ProposalPromotionPlan[PredicateProposalRef],
) -> ProposalPromotionResult[PredicateProposalRef]:
    if not plan.items:
        return ProposalPromotionResult(0, plan.branch, ())
    if plan.proposal_tip is None:
        raise ValueError("predicate proposal promotion requires a proposal tip")

    proposal_documents = {
        item.ref: repo.families.proposal_predicates.require(
            item.ref,
            commit=plan.proposal_tip,
        )
        for item in plan.items
    }
    transition_records: list[PredicateProposalTransitionRecord] = []
    for item in plan.items:
        proposal = proposal_documents[item.ref]
        declarations = {
            declaration.name: declaration
            for declaration in proposal.proposed_declarations
        }
        transition_records.append(
            PredicateProposalTransitionRecord(
                name=item.predicate_id,
                source_paper=item.source_paper,
                declaration=declarations[item.predicate_id],
            )
        )

    batch_result = run_transition_batch(
        charter=PREDICATE_PROPOSAL_CHARTER,
        transition="promote_proposal",
        records=tuple(transition_records),
        context=TransitionContext(metadata={"proposal_tip": plan.proposal_tip}),
        callbacks=LifecycleCallbacks(
            materializers={
                "predicate_proposal_to_canonical": _materialize_predicate_proposal,
            },
        ),
    )
    writes = tuple(
        write
        for item_result in batch_result.items
        for write in item_result.plan.writes
    )

    git = repo.git
    if git is None:
        raise ValueError("predicate proposal promotion requires a git-backed repository")
    with _PREDICATE_MUTATION_LOCK, git.head_bound_transaction(
        repo.require_git().primary_branch_name(),
    ) as head_txn:
        for write in writes:
            reject_predicate_document_conflicts(
                repo,
                commit=head_txn.expected_head,
                target_ref=PredicateRef(write.identity),
                document=cast(PredicateDocument, write.record),
            )

        if writes:
            with head_txn.families_transact(
                repo.families,
                message=f"Promote {len(plan.items)} predicate proposal(s) from {plan.branch}",
            ) as transaction:
                for write in writes:
                    _save_predicate_promotion_write(transaction, write)
    return ProposalPromotionResult(len(plan.items), plan.branch, plan.items)


def _materialize_predicate_proposal(
    record: object,
    context: TransitionContext,
) -> TransitionPlan:
    proposal_tip = context.metadata.get("proposal_tip")
    if not isinstance(proposal_tip, str) or not proposal_tip:
        raise ValueError("predicate proposal transition requires proposal_tip metadata")
    proposal_record = cast(PredicateProposalTransitionRecord, record)
    declaration = proposal_record.declaration
    document = PredicateDocument(
        id=declaration.name,
        arity=declaration.arity,
        arg_types=tuple(str(arg_type) for arg_type in declaration.arg_types),
        description=declaration.description,
        authoring_group=proposal_record.source_paper,
        promoted_from_sha=proposal_tip,
    )
    return TransitionPlan(
        writes=(
            FamilyRecordWrite(
                family="predicates",
                identity=declaration.name,
                state="canonical",
                record=document,
            ),
        )
    )


def _save_predicate_promotion_write(transaction: Any, write: FamilyRecordWrite) -> None:
    if write.family != "predicates":
        raise ValueError(f"unknown predicate proposal write family: {write.family!r}")
    transaction.predicates.save(
        PredicateRef(write.identity),
        cast(PredicateDocument, write.record),
    )

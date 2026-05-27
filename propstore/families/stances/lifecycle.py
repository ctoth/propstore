from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, TYPE_CHECKING, cast

from quire.documents import convert_document_value, document_to_payload
from quire.lifecycle import (
    FamilyRecordWrite,
    LifecycleCallbacks,
    TransitionContext,
    TransitionPlan,
    run_transition_batch,
)
from quire.references import FamilyReferenceIndex

from propstore.families.claims.declaration import SourceClaimDocument
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.identity.stances import stamp_stance_artifact_id
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PROPOSAL_STANCE_BRANCH,
    PropstoreFamily,
    StanceRef,
)
from propstore.families.stances.declaration import (
    STANCE_CHARTER,
    SourceStanceEntryDocument,
    StanceDocument,
)
from propstore.proposal_lifecycle import (
    ProposalAlreadyPromoted,
    ProposalPromotionItem,
    ProposalPromotionPlan,
    ProposalPromotionResult,
    UnknownProposalPath,
)
from propstore.opinion import Opinion
from propstore.stances import StanceType

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class StanceProposalInput:
    target: str
    type: StanceType | str
    source_claim: str | None = None
    perspective_source_claim_id: str | None = None
    strength: str | None = None
    note: str | None = None
    conditions_differ: str | None = None
    opinion: Opinion | None = None
    resolution: Mapping[str, object] | None = None
    target_justification_id: str | None = None
    artifact_code: str | None = None


@dataclass(frozen=True)
class StanceProposalTransitionRecord:
    id: str
    document: StanceDocument


def stance_proposal_filename(artifact_id: str) -> str:
    return Path(stance_proposal_relpath(artifact_id)).name


def stance_proposal_relpath(artifact_id: str) -> str:
    family = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.PROPOSAL_STANCES).artifact_family
    return family.address_for(cast(Any, None), StanceRef(artifact_id)).require_path()


def stance_proposal_branch() -> str:
    branch = PROPOSAL_STANCE_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("proposal stance branch placement must be fixed")
    return branch


def _coerce_stance_proposal_input(stance: Mapping[str, object]) -> StanceProposalInput:
    target = stance.get("target")
    stance_type = stance.get("type")
    if not isinstance(target, str) or not target:
        raise ValueError("stance proposal target must be a non-empty string")
    if not isinstance(stance_type, (str, StanceType)):
        raise ValueError("stance proposal type must be a non-empty string")
    return StanceProposalInput(
        target=target,
        type=stance_type,
        source_claim=_optional_str(stance.get("source_claim")),
        perspective_source_claim_id=_optional_str(stance.get("perspective_source_claim_id")),
        strength=_optional_str(stance.get("strength")),
        note=_optional_str(stance.get("note")),
        conditions_differ=_optional_str(stance.get("conditions_differ")),
        opinion=cast(Opinion | None, stance.get("opinion")),
        resolution=_optional_mapping(stance.get("resolution")),
        target_justification_id=_optional_str(stance.get("target_justification_id")),
        artifact_code=_optional_str(stance.get("artifact_code")),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"expected string or null, got {type(value).__name__}")
    return value


def _optional_mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"expected mapping or null, got {type(value).__name__}")
    return value


def build_stance_proposal_document(
    source_claim_id: str,
    stance: StanceProposalInput,
    model_name: str,
) -> StanceDocument:
    payload = {
        "source_claim": stance.source_claim or source_claim_id,
        "target": stance.target,
        "type": stance.type,
        "perspective_source_claim_id": stance.perspective_source_claim_id,
        "strength": stance.strength,
        "note": stance.note,
        "conditions_differ": stance.conditions_differ,
        "opinion": stance.opinion,
        "resolution": stance.resolution,
        "target_justification_id": stance.target_justification_id,
        "artifact_code": stance.artifact_code,
        "classification_model": model_name,
        "classification_date": str(date.today()),
    }
    stamped = stamp_stance_artifact_id(payload)
    artifact_id = stamped["artifact_code"]
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("stance proposal document missing artifact_code")
    return convert_document_value(
        stamped,
        StanceDocument,
        source=stance_proposal_relpath(artifact_id),
    )


def plan_stance_proposal_promotion(
    repo: "Repository",
    *,
    path: str | None = None,
) -> ProposalPromotionPlan[StanceRef]:
    proposal_branch = stance_proposal_branch()
    proposal_tip = repo.require_git().branch_sha(proposal_branch)
    if proposal_tip is None:
        return ProposalPromotionPlan(
            branch=proposal_branch,
            proposal_tip=None,
            items=(),
        )

    available_refs = repo.families.proposal_stances.iter(
        branch=proposal_branch,
        commit=proposal_tip,
    )
    available_by_name = {
        stance_proposal_filename(ref.artifact_id): ref
        for ref in available_refs
    }
    if path is not None:
        requested_name = Path(path).name
        if not requested_name.endswith(".yaml"):
            requested_name = stance_proposal_filename(requested_name)
        if requested_name not in available_by_name:
            raise UnknownProposalPath(path, tuple(sorted(available_by_name)))
        selected_refs = [available_by_name[requested_name]]
    else:
        selected_refs = [available_by_name[name] for name in sorted(available_by_name)]

    items: list[ProposalPromotionItem[StanceRef]] = []
    for ref in selected_refs:
        filename = stance_proposal_filename(ref.artifact_id)
        target_relpath = repo.families.stances.address(StanceRef(ref.artifact_id)).require_path()
        proposal_document = repo.families.proposal_stances.require(
            ref,
            commit=proposal_tip,
        )
        items.append(
            ProposalPromotionItem(
                ref=ref,
                artifact_id=ref.artifact_id,
                source_claim=proposal_document.source_claim or "",
                source_relpath=f"{proposal_branch}:{repo.families.proposal_stances.address(ref).require_path()}",
                target_path=repo.root / target_relpath,
                filename=filename,
            )
        )
    return ProposalPromotionPlan(
        branch=proposal_branch,
        proposal_tip=proposal_tip,
        items=tuple(items),
    )


def promote_stance_proposals(
    repo: "Repository",
    plan: ProposalPromotionPlan[StanceRef],
    *,
    force: bool = False,
) -> ProposalPromotionResult[StanceRef]:
    moved = len(plan.items)
    if moved > 0:
        if plan.proposal_tip is None:
            raise ValueError("stance proposal promotion requires a proposal tip")
        proposal_records: list[StanceProposalTransitionRecord] = []
        for item in plan.items:
            existing = repo.families.stances.load(item.ref)
            if (
                existing is not None
                and existing.promoted_from_sha is not None
                and not force
            ):
                raise ProposalAlreadyPromoted(
                    item.artifact_id,
                    existing.promoted_from_sha,
                )
            proposal_document = repo.families.proposal_stances.require(
                item.ref,
                commit=plan.proposal_tip,
            )
            proposal_records.append(
                StanceProposalTransitionRecord(
                    id=item.artifact_id,
                    document=proposal_document,
                )
            )
        batch_result = run_transition_batch(
            charter=STANCE_CHARTER,
            transition="promote_proposal",
            records=tuple(proposal_records),
            context=TransitionContext(metadata={"proposal_tip": plan.proposal_tip}),
            callbacks=LifecycleCallbacks(
                materializers={
                    "stance_proposal_to_canonical": _materialize_stance_proposal,
                },
            ),
        )
        writes = tuple(
            write
            for item_result in batch_result.items
            for write in item_result.plan.writes
        )
        if writes:
            with repo.families.transact(
                message=f"Promote {moved} stance proposal file(s) from {plan.branch}",
            ) as transaction:
                for write in writes:
                    _save_stance_promotion_write(transaction, write)
    return ProposalPromotionResult(
        moved=moved,
        branch=plan.branch,
        promoted_items=plan.items,
    )


def _materialize_stance_proposal(
    record: object,
    context: TransitionContext,
) -> TransitionPlan:
    proposal_tip = context.metadata.get("proposal_tip")
    if not isinstance(proposal_tip, str) or not proposal_tip:
        raise ValueError("stance proposal transition requires proposal_tip metadata")
    proposal_record = cast(StanceProposalTransitionRecord, record)
    proposal = proposal_record.document
    document = StanceDocument(
        artifact_id=proposal.artifact_id,
        source_claim=proposal.source_claim,
        perspective_source_claim_id=proposal.perspective_source_claim_id,
        target=proposal.target,
        type=proposal.type,
        strength=proposal.strength,
        note=proposal.note,
        conditions_differ=proposal.conditions_differ,
        resolution=proposal.resolution,
        target_justification_id=proposal.target_justification_id,
        artifact_code=proposal.artifact_code,
        classification_model=proposal.classification_model,
        classification_date=proposal.classification_date,
        promoted_from_sha=proposal_tip,
    )
    return TransitionPlan(
        writes=(
            FamilyRecordWrite(
                family="stances",
                identity=proposal.artifact_id,
                state="canonical",
                record=document,
            ),
        )
    )


def _save_stance_promotion_write(transaction: Any, write: FamilyRecordWrite) -> None:
    if write.family != "stances":
        raise ValueError(f"unknown stance proposal write family: {write.family!r}")
    transaction.stances.save(
        StanceRef(write.identity),
        cast(StanceDocument, write.record),
    )


def commit_stance_proposals(
    repo: "Repository",
    stances_by_claim: Mapping[str, Sequence[Mapping[str, object]]],
    model_name: str,
    *,
    branch: str | None = None,
) -> tuple[str | None, list[str]]:
    if not stances_by_claim:
        return None, []

    target_branch = stance_proposal_branch() if branch is None else branch
    proposal_documents: list[StanceDocument] = []
    for source_claim_id, stances in sorted(stances_by_claim.items()):
        for stance in stances:
            proposal_documents.append(
                build_stance_proposal_document(
                    source_claim_id,
                    _coerce_stance_proposal_input(stance),
                    model_name,
                )
            )
    if not proposal_documents:
        return None, []

    sha: str | None = None
    with repo.families.transact(
        message=(
            f"Record {len(proposal_documents)} stance proposal artifact(s)"
            if len(proposal_documents) != 1
            else "Record stance proposal artifact"
        ),
        branch=target_branch,
    ) as transaction:
        relpaths: list[str] = []
        for document in proposal_documents:
            artifact_id = document.artifact_code
            if not isinstance(artifact_id, str) or not artifact_id:
                raise ValueError("stance proposal document missing artifact_code")
            ref = StanceRef(artifact_id)
            transaction.proposal_stances.save(
                ref,
                document,
            )
            relpaths.append(repo.families.proposal_stances.address(ref).require_path())
        transaction.transaction.commit()
        sha = transaction.commit_sha
    if sha is None:
        raise ValueError("stance proposal transaction did not produce a commit")
    return sha, sorted(relpaths)


def normalize_source_stances_payload(
    data: tuple[SourceStanceEntryDocument, ...],
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Any] | None = None,
) -> tuple[SourceStanceEntryDocument, ...]:
    normalized_stances: list[SourceStanceEntryDocument] = []
    for index, stance in enumerate(data, start=1):
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        normalized = cast(dict[str, Any], document_to_payload(stance))
        normalized["source_claim"] = claim_index.require_id(stance.source_claim)
        target = resolve_first_claim_reference_id(
            stance.target,
            claim_index,
            primary_claim_index,
        )
        if target is None:
            raise ValueError(f"unresolved stance target: {stance.target}")
        normalized["target"] = target
        normalized_stances.append(
            convert_document_value(
                normalized,
                SourceStanceEntryDocument,
                source=f"stances[{index}]",
            )
        )
    return tuple(normalized_stances)

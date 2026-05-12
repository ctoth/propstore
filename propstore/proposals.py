"""Helpers for committed proposal artifacts.

Proposal artifacts are durable git state on dedicated proposal branches,
not ambient files in the working tree.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from quire.documents import encode_document
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY, PROPOSAL_STANCE_BRANCH, PropstoreFamily
from propstore.families.registry import StanceRef
from propstore.families.documents.stances import StanceDocument
from propstore.families.identity.stances import stamp_stance_artifact_id
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    commit_planned_canonical_artifacts,
)
from quire.documents import convert_document_value

if TYPE_CHECKING:
    from propstore.repository import Repository


def stance_proposal_filename(artifact_id: str) -> str:
    """Return the proposal filename for a stance artifact."""
    return Path(stance_proposal_relpath(artifact_id)).name


def stance_proposal_relpath(artifact_id: str) -> str:
    """Return the repo-relative stance proposal path."""
    family = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.PROPOSAL_STANCES).artifact_family
    return family.address_for(cast(Any, object()), StanceRef(artifact_id)).require_path()


def stance_proposal_branch() -> str:
    """Return the proposal branch declared by the stance proposal placement."""
    branch = PROPOSAL_STANCE_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("proposal stance branch placement must be fixed")
    return branch


@dataclass(frozen=True)
class StanceProposalPromotionItem:
    artifact_id: str
    source_claim: str
    source_relpath: str
    target_path: Path
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


class UnknownProposalPath(ValueError):
    def __init__(self, requested_path: str, available_filenames: tuple[str, ...]) -> None:
        self.requested_path = requested_path
        self.available_filenames = available_filenames
        available = ", ".join(available_filenames) if available_filenames else "<none>"
        super().__init__(
            f"Unknown stance proposal path {requested_path!r}; available: {available}"
        )


class ProposalAlreadyPromoted(ValueError):
    def __init__(self, artifact_id: str, promoted_from_sha: str) -> None:
        self.artifact_id = artifact_id
        self.promoted_from_sha = promoted_from_sha
        super().__init__(
            f"Stance proposal {artifact_id!r} was already promoted from {promoted_from_sha}"
        )


def plan_stance_proposal_promotion(
    repo: Repository,
    *,
    path: str | None = None,
) -> StanceProposalPromotionPlan:
    proposal_branch = stance_proposal_branch()
    proposal_tip = repo.snapshot.branch_head(proposal_branch)
    if proposal_tip is None:
        return StanceProposalPromotionPlan(
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

    items: list[StanceProposalPromotionItem] = []
    for ref in selected_refs:
        filename = stance_proposal_filename(ref.artifact_id)
        target_relpath = repo.families.stances.address(StanceRef(ref.artifact_id)).require_path()
        proposal_document = repo.families.proposal_stances.require(
            ref,
            commit=proposal_tip,
        )
        items.append(
            StanceProposalPromotionItem(
                artifact_id=ref.artifact_id,
                source_claim=proposal_document.source_claim or "",
                source_relpath=f"{proposal_branch}:{repo.families.proposal_stances.address(ref).require_path()}",
                target_path=repo.root / target_relpath,
                filename=filename,
            )
        )
    return StanceProposalPromotionPlan(
        branch=proposal_branch,
        proposal_tip=proposal_tip,
        items=tuple(items),
    )


def promote_stance_proposals(
    repo: Repository,
    plan: StanceProposalPromotionPlan,
    *,
    force: bool = False,
) -> StanceProposalPromotionResult:
    moved = len(plan.items)
    if moved > 0:
        if plan.proposal_tip is None:
            raise ValueError("stance proposal promotion requires a proposal tip")
        artifacts: list[PlannedCanonicalArtifact[StanceRef, StanceDocument]] = []
        for item in plan.items:
            ref = StanceRef(item.artifact_id)
            existing = repo.families.stances.load(ref)
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
                ref,
                commit=plan.proposal_tip,
            )
            artifacts.append(
                PlannedCanonicalArtifact(
                    ref,
                    StanceDocument(
                        source_claim=proposal_document.source_claim,
                        perspective_source_claim_id=proposal_document.perspective_source_claim_id,
                        target=proposal_document.target,
                        type=proposal_document.type,
                        strength=proposal_document.strength,
                        note=proposal_document.note,
                        conditions_differ=proposal_document.conditions_differ,
                        resolution=proposal_document.resolution,
                        target_justification_id=proposal_document.target_justification_id,
                        artifact_code=proposal_document.artifact_code,
                        classification_model=proposal_document.classification_model,
                        classification_date=proposal_document.classification_date,
                        promoted_from_sha=plan.proposal_tip,
                    ),
                )
            )
        commit_planned_canonical_artifacts(
            repo.families.transact,
            message=f"Promote {moved} stance proposal file(s) from {plan.branch}",
            family=lambda transaction: transaction.stances,
            artifacts=artifacts,
        )
    return StanceProposalPromotionResult(
        moved=moved,
        branch=plan.branch,
        promoted_items=plan.items,
    )


def build_stance_document(
    source_claim_id: str,
    stance: dict,
    model_name: str,
    ) -> StanceDocument:
    """Build the persisted typed payload for a stance proposal."""
    payload = {
        **stance,
        "source_claim": stance.get("source_claim") or source_claim_id,
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


def dump_yaml_bytes(document: object) -> bytes:
    """Serialize a typed proposal document to YAML bytes."""
    return encode_document(document)


def commit_stance_proposals(
    repo: Repository,
    stances_by_claim: Mapping[str, list[dict]],
    model_name: str,
    *,
    branch: str | None = None,
) -> tuple[str | None, list[str]]:
    """Commit stance proposal snapshots to the proposal branch."""
    if not stances_by_claim:
        return None, []

    target_branch = stance_proposal_branch() if branch is None else branch
    proposal_documents: list[StanceDocument] = []
    for source_claim_id, stances in sorted(stances_by_claim.items()):
        for stance in stances:
            proposal_documents.append(
                build_stance_document(source_claim_id, stance, model_name)
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

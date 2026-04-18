"""Helpers for committed proposal artifacts.

Proposal artifacts are durable git state on dedicated proposal branches,
not ambient files in the working tree.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, cast

from quire.documents import encode_document
from propstore.artifacts.families import PROPOSAL_STANCE_FAMILY
from propstore.artifacts.families import StanceFileRef
from propstore.artifacts.documents.stances import StanceFileDocument
from quire.documents import convert_document_value

if TYPE_CHECKING:
    from propstore.repository import Repository


def stance_proposal_filename(source_claim_id: str) -> str:
    """Return the proposal filename for a source claim."""
    return Path(stance_proposal_relpath(source_claim_id)).name


def stance_proposal_relpath(source_claim_id: str) -> str:
    """Return the repo-relative stance proposal path."""
    return PROPOSAL_STANCE_FAMILY.address_for(
        cast("Repository", object()),
        StanceFileRef(source_claim_id),
    ).require_path()


def stance_proposal_branch(repo: Repository | None = None) -> str:
    """Return the proposal branch declared by the stance proposal placement."""
    return PROPOSAL_STANCE_FAMILY.address_for(
        cast("Repository", object()) if repo is None else repo,
        StanceFileRef("placeholder"),
    ).branch


@dataclass(frozen=True)
class StanceProposalPromotionItem:
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


def plan_stance_proposal_promotion(
    repo: Repository,
    *,
    path: str | None = None,
) -> StanceProposalPromotionPlan:
    proposal_branch = stance_proposal_branch(repo)
    proposal_tip = repo.snapshot.branch_head(proposal_branch)
    if proposal_tip is None:
        return StanceProposalPromotionPlan(
            branch=proposal_branch,
            proposal_tip=None,
            items=(),
        )

    available_refs = repo.families.proposal_stances.list(
        branch=proposal_branch,
        commit=proposal_tip,
    )
    available_by_name = {
        stance_proposal_filename(ref.source_claim): ref
        for ref in available_refs
    }
    if path is not None:
        requested_name = Path(path).name
        if not requested_name.endswith(".yaml"):
            requested_name = stance_proposal_filename(requested_name)
        selected_refs = (
            [available_by_name[requested_name]]
            if requested_name in available_by_name
            else []
        )
    else:
        selected_refs = [available_by_name[name] for name in sorted(available_by_name)]

    items: list[StanceProposalPromotionItem] = []
    for ref in selected_refs:
        filename = stance_proposal_filename(ref.source_claim)
        target_relpath = repo.families.stances.address(StanceFileRef(ref.source_claim)).require_path()
        items.append(
            StanceProposalPromotionItem(
                source_claim=ref.source_claim,
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
) -> StanceProposalPromotionResult:
    moved = len(plan.items)
    if moved > 0:
        if plan.proposal_tip is None:
            raise ValueError("stance proposal promotion requires a proposal tip")
        with repo.families.transact(
            message=f"Promote {moved} stance proposal file(s) from {plan.branch}",
        ) as transaction:
            for item in plan.items:
                ref = StanceFileRef(item.source_claim)
                transaction.stances.save(
                    ref,
                    repo.families.proposal_stances.require(ref, commit=plan.proposal_tip),
                )
        repo.snapshot.sync_worktree()
    return StanceProposalPromotionResult(
        moved=moved,
        branch=plan.branch,
    )


def build_stance_document(
    source_claim_id: str,
    stances: list[dict],
    model_name: str,
    ) -> StanceFileDocument:
    """Build the persisted typed payload for a stance proposal."""
    return convert_document_value(
        {
            "source_claim": source_claim_id,
            "classification_model": model_name,
            "classification_date": str(date.today()),
            "stances": stances,
        },
        StanceFileDocument,
        source=stance_proposal_relpath(source_claim_id),
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
) -> tuple[str, list[str]]:
    """Commit stance proposal snapshots to the proposal branch."""
    if not stances_by_claim:
        raise ValueError("stances_by_claim must not be empty")

    target_branch = stance_proposal_branch(repo) if branch is None else branch
    with repo.families.transact(
        message=(
            f"Record {len(stances_by_claim)} stance proposal file(s)"
            if len(stances_by_claim) != 1
            else f"Record stance proposal for {next(iter(stances_by_claim))}"
        ),
        branch=target_branch,
    ) as transaction:
        relpaths: list[str] = []
        for source_claim_id, stances in sorted(stances_by_claim.items()):
            ref = StanceFileRef(source_claim_id)
            transaction.proposal_stances.save(
                ref,
                build_stance_document(source_claim_id, stances, model_name),
            )
            relpaths.append(repo.families.proposal_stances.address(ref).require_path())
    sha = transaction.commit_sha
    if sha is None:
        raise ValueError("stance proposal transaction did not produce a commit")
    return sha, sorted(relpaths)

"""Helpers for committed proposal artifacts.

Proposal artifacts are durable git state on dedicated proposal branches,
not ambient files in the working tree.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import TYPE_CHECKING

from propstore.artifacts import PROPOSAL_STANCE_FAMILY, STANCE_PROPOSAL_BRANCH, StanceFileRef

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


def stance_proposal_filename(source_claim_id: str) -> str:
    """Return the proposal filename for a source claim."""
    safe_name = source_claim_id.replace(":", "__")
    return f"{safe_name}.yaml"


def stance_proposal_relpath(source_claim_id: str) -> str:
    """Return the repo-relative stance proposal path."""
    return f"stances/{stance_proposal_filename(source_claim_id)}"


def build_stance_document(
    source_claim_id: str,
    stances: list[dict],
    model_name: str,
    *,
    repo: Repository,
):
    """Build the persisted typed payload for a stance proposal."""
    return repo.artifacts.coerce(
        PROPOSAL_STANCE_FAMILY,
        {
            "source_claim": source_claim_id,
            "classification_model": model_name,
            "classification_date": str(date.today()),
            "stances": stances,
        },
        source=stance_proposal_relpath(source_claim_id),
    )


def commit_stance_proposals(
    repo: Repository,
    stances_by_claim: Mapping[str, list[dict]],
    model_name: str,
    *,
    branch: str = STANCE_PROPOSAL_BRANCH,
) -> tuple[str, list[str]]:
    """Commit stance proposal snapshots to the proposal branch."""
    if not stances_by_claim:
        raise ValueError("stances_by_claim must not be empty")

    transaction = repo.artifacts.transact(
        message=(
            f"Record {len(stances_by_claim)} stance proposal file(s)"
            if len(stances_by_claim) != 1
            else f"Record stance proposal for {next(iter(stances_by_claim))}"
        ),
        branch=branch,
    )
    relpaths: list[str] = []
    for source_claim_id, stances in sorted(stances_by_claim.items()):
        ref = StanceFileRef(source_claim_id)
        transaction.save(
            PROPOSAL_STANCE_FAMILY,
            ref,
            build_stance_document(source_claim_id, stances, model_name, repo=repo),
        )
        relpaths.append(repo.artifacts.resolve(PROPOSAL_STANCE_FAMILY, ref).relpath)
    sha = transaction.commit()
    return sha, sorted(relpaths)

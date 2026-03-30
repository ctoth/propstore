"""Helpers for committed proposal artifacts.

Proposal artifacts are durable git state on dedicated proposal branches,
not ambient files in the working tree.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import date

import yaml

from propstore.repo.branch import branch_head, create_branch

STANCE_PROPOSAL_BRANCH = "proposal/stances"


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
) -> dict:
    """Build the persisted YAML payload for a stance proposal."""
    return {
        "source_claim": source_claim_id,
        "classification_model": model_name,
        "classification_date": str(date.today()),
        "stances": stances,
    }


def dump_yaml_bytes(data: dict) -> bytes:
    """Serialize YAML consistently for committed proposal artifacts."""
    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")


def commit_stance_proposals(
    git,
    stances_by_claim: Mapping[str, list[dict]],
    model_name: str,
    *,
    branch: str = STANCE_PROPOSAL_BRANCH,
) -> tuple[str, list[str]]:
    """Commit stance proposal snapshots to the proposal branch."""
    if not stances_by_claim:
        raise ValueError("stances_by_claim must not be empty")
    if branch_head(git, branch) is None:
        create_branch(git, branch)

    adds = {
        stance_proposal_relpath(source_claim_id): dump_yaml_bytes(
            build_stance_document(source_claim_id, stances, model_name)
        )
        for source_claim_id, stances in stances_by_claim.items()
    }
    commit_message = (
        f"Record {len(adds)} stance proposal file(s)"
        if len(adds) != 1
        else f"Record stance proposal for {next(iter(stances_by_claim))}"
    )
    sha = git.commit_batch(adds=adds, deletes=[], message=commit_message, branch=branch)
    return sha, sorted(adds)

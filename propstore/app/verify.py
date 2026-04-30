"""Application-layer verification workflows."""

from __future__ import annotations

from propstore.repository import Repository


def verify_claim_tree(repo: Repository, claim_ref: str, *, commit: str | None = None):
    from propstore.artifact_verification import verify_claim_tree as run_verify_claim_tree

    return run_verify_claim_tree(repo, claim_ref, commit=commit)

"""Merge commit creation for propstore knowledge repositories."""
from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING

from propstore.artifacts.families import CLAIMS_FILE_FAMILY, MERGE_MANIFEST_FAMILY
from propstore.artifacts.refs import ClaimsFileRef, MergeManifestRef
from propstore.merge.merge_classifier import build_merge_framework
from propstore.merge.merge_report import semantic_candidate_details

if TYPE_CHECKING:
    from propstore.storage.snapshot import RepositorySnapshot


def create_merge_commit(
    snapshot: RepositorySnapshot,
    branch_a: str,
    branch_b: str,
    message: str = "",
    *,
    target_branch: str | None = None,
) -> str:
    """Create a two-parent merge commit from the formal merge object."""
    from propstore.artifacts.store import create_artifact_store_for_git

    kr = snapshot.git
    artifacts = create_artifact_store_for_git(kr)
    if target_branch is None:
        target_branch = snapshot.primary_branch_name()
    merge = build_merge_framework(snapshot, branch_a, branch_b)

    left_sha = snapshot.branch_head(branch_a)
    right_sha = snapshot.branch_head(branch_b)
    if left_sha is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if right_sha is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    left_entries = kr.flat_tree_entries(left_sha)
    right_entries = kr.flat_tree_entries(right_sha)

    merged_entries: dict[str, str] = {}
    for path, sha in right_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha
    for path, sha in left_entries.items():
        if not path.startswith("claims/"):
            merged_entries[path] = sha

    sorted_arguments = sorted(merge.arguments, key=lambda argument: argument.claim_id)
    artifact_counts = Counter(argument.artifact_id for argument in sorted_arguments)
    merged_claims = [
        argument.claim.to_payload()
        for argument in sorted_arguments
        if artifact_counts[argument.artifact_id] == 1
    ]

    claims_payload = {
        "source": {
            "paper": "merged",
            "extraction_model": "merge",
            "extraction_date": time.strftime("%Y-%m-%d"),
        },
        "claims": merged_claims,
    }
    claim_paths = [path for path in merged_entries if path.startswith("claims/")]
    for path in claim_paths:
        del merged_entries[path]

    claims_ref = ClaimsFileRef("merged")
    claims_document = artifacts.coerce(
        CLAIMS_FILE_FAMILY,
        claims_payload,
        source=artifacts.resolve(CLAIMS_FILE_FAMILY, claims_ref).relpath,
    )

    manifest_payload = {
        "merge": {
            "branch_a": branch_a,
            "branch_b": branch_b,
            "arguments": [
                {
                    "claim_id": argument.claim_id,
                    "canonical_claim_id": argument.canonical_claim_id,
                    "artifact_id": argument.artifact_id,
                    "logical_id": argument.logical_id,
                    "branch_origins": list(argument.branch_origins),
                    "materialized": artifact_counts[argument.artifact_id] == 1,
                }
                for argument in sorted_arguments
            ],
            "semantic_candidates": [list(group) for group in merge.semantic_candidates],
            "semantic_candidate_details": semantic_candidate_details(merge),
        }
    }
    manifest_document = artifacts.coerce(
        MERGE_MANIFEST_FAMILY,
        manifest_payload,
        source="merge/manifest.yaml",
    )

    prepared_claims = artifacts.prepare(
        CLAIMS_FILE_FAMILY,
        claims_ref,
        claims_document,
        branch=target_branch,
    )
    prepared_manifest = artifacts.prepare(
        MERGE_MANIFEST_FAMILY,
        MergeManifestRef(),
        manifest_document,
        branch=target_branch,
    )

    for prepared in (prepared_claims, prepared_manifest):
        merged_entries[prepared.resolved.relpath] = kr.store_blob(prepared.content)

    return kr.commit_flat_tree(
        merged_entries,
        message or f"Merge {branch_a} and {branch_b}",
        parents=[left_sha, right_sha],
        branch=target_branch,
    )

"""Merge commit creation for propstore knowledge repositories."""
from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING

from dulwich.objects import Blob, Commit

from propstore.artifacts.families import CLAIMS_FILE_FAMILY, MERGE_MANIFEST_FAMILY
from propstore.artifacts.refs import ClaimsFileRef, MergeManifestRef
from propstore.storage.git_backend import _DEFAULT_AUTHOR, _ref_set
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
    from propstore.artifacts.store import ArtifactRepository

    kr = snapshot.git
    artifacts = ArtifactRepository.for_git(kr)
    if target_branch is None:
        target_branch = snapshot.primary_branch_name()
    merge = build_merge_framework(snapshot, branch_a, branch_b)

    left_sha = snapshot.branch_head(branch_a)
    right_sha = snapshot.branch_head(branch_b)
    if left_sha is None:
        raise ValueError(f"Branch {branch_a!r} does not exist")
    if right_sha is None:
        raise ValueError(f"Branch {branch_b!r} does not exist")

    left_entries: dict[str, bytes] = {}
    left_tree = kr._get_tree(left_sha)
    if left_tree is not None:
        kr._flatten_tree(left_tree, "", left_entries)

    right_entries: dict[str, bytes] = {}
    right_tree = kr._get_tree(right_sha)
    if right_tree is not None:
        kr._flatten_tree(right_tree, "", right_entries)

    merged_entries: dict[str, bytes] = {}
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
        blob = Blob.from_string(prepared.content)
        kr._repo.object_store.add_object(blob)
        merged_entries[prepared.resolved.relpath] = blob.id

    store = kr._repo.object_store
    root_tree = kr._build_tree_from_flat(merged_entries, store)

    commit = Commit()
    commit.tree = root_tree.id
    commit.author = _DEFAULT_AUTHOR
    commit.committer = _DEFAULT_AUTHOR
    commit.encoding = b"UTF-8"
    commit.message = (message or f"Merge {branch_a} and {branch_b}").encode("utf-8")

    now = int(time.time())
    commit.commit_time = now
    commit.author_time = now
    commit.commit_timezone = 0
    commit.author_timezone = 0
    commit.parents = [left_sha.encode("ascii"), right_sha.encode("ascii")]
    store.add_object(commit)

    target_ref = f"refs/heads/{target_branch}".encode("ascii")
    _ref_set(kr._repo.refs, target_ref, commit.id)
    return commit.id.decode("ascii")

"""Application-layer repository merge workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from propstore.families.registry import MergeManifestRef
from propstore.repository import Repository


@dataclass(frozen=True)
class MergeInspectRequest:
    branch_a: str
    branch_b: str
    semantics: str = "grounded"


@dataclass(frozen=True)
class MergeInspectReport:
    payload: Mapping[str, object]


@dataclass(frozen=True)
class MergeCommitRequest:
    branch_a: str
    branch_b: str
    message: str = ""
    target_branch: str | None = None


@dataclass(frozen=True)
class MergeCommitReport:
    payload: Mapping[str, object]


def inspect_merge(
    repo: Repository,
    request: MergeInspectRequest,
) -> MergeInspectReport:
    from propstore.merge.merge_classifier import build_merge_framework
    from propstore.merge.merge_report import summarize_merge_framework

    merge_framework = build_merge_framework(
        repo.snapshot,
        request.branch_a,
        request.branch_b,
    )
    return MergeInspectReport(
        payload=summarize_merge_framework(
            merge_framework,
            semantics=request.semantics,
        )
    )


def commit_merge(
    repo: Repository,
    request: MergeCommitRequest,
) -> MergeCommitReport:
    from propstore.storage.merge_commit import create_merge_commit

    target_branch = request.target_branch or repo.snapshot.primary_branch_name()
    commit_sha = create_merge_commit(
        repo.snapshot,
        request.branch_a,
        request.branch_b,
        message=request.message,
        target_branch=target_branch,
    )
    manifest = repo.families.merge_manifests.require(
        MergeManifestRef(),
        commit=commit_sha,
    )
    git = repo.git
    if git is None:
        raise ValueError("merge commit report requires a git-backed repository")
    claim_paths = sorted(
        path
        for path in git.flat_tree_entries(commit_sha)
        if path.startswith("claims/")
    )
    return MergeCommitReport(
        payload={
            "surface": "storage_merge_commit",
            "branch_a": request.branch_a,
            "branch_b": request.branch_b,
            "target_branch": target_branch,
            "claims_paths": claim_paths,
            "manifest_path": repo.families.merge_manifests.family.address_for(
                repo,
                MergeManifestRef(),
            ).require_path(),
            "commit_sha": commit_sha,
            "semantic_candidate_count": len(
                manifest.merge.semantic_candidate_details
            ),
        }
    )

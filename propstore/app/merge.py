"""Application-layer repository merge facade (Phase 10-1).

The ``pks merge commit`` adapter needs a rich report, but the storage core
:func:`~propstore.merge.create_merge_commit` returns only the merge commit sha.
This facade calls that core and then reads the resulting tree back into a typed
:class:`MergeCommitReport` — the surviving claim blob paths, the materialized
manifest path, and the semantic-candidate count from the formal framework. It is
owner-layer (no Click / stdout / ``sys.exit``); the CLI adapter renders it.

``merge inspect`` needs no facade: it adapts
:func:`~propstore.merge.summarize_merge_framework` over
:func:`~propstore.merge.build_repository_merge_framework` directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from propstore.families.claims import Claim
from propstore.families.merge_manifests import MergeManifest
from propstore.merge import build_repository_merge_framework, create_merge_commit
from propstore.reporting import JsonReportMixin

if TYPE_CHECKING:
    from propstore.repository import Repository

_CLAIM_ROOT = Claim.__charter__.family.storage_root()
_MANIFEST_ROOT = MergeManifest.__charter__.family.storage_root()


@dataclass(frozen=True)
class MergeCommitRequest:
    branch_a: str
    branch_b: str
    message: str = ""
    target_branch: str | None = None


@dataclass(frozen=True)
class MergeCommitReport(JsonReportMixin):
    surface: str
    branch_a: str
    branch_b: str
    target_branch: str
    commit_sha: str
    claims_paths: tuple[str, ...]
    manifest_path: str | None
    semantic_candidate_count: int


def _entries_under(paths: list[str], root: str) -> list[str]:
    prefix = f"{root}/"
    return sorted(path for path in paths if path == root or path.startswith(prefix))


def commit_merge(
    repo: Repository,
    request: MergeCommitRequest,
) -> MergeCommitReport:
    """Create the two-parent merge commit and read its tree into a typed report.

    Holds non-commitment: the report enumerates *every* surviving rival claim
    blob rather than a single winner, mirroring what
    :func:`create_merge_commit` materialized.
    """

    git = repo.require_git()
    target_branch = request.target_branch or git.primary_branch_name()
    commit_sha = create_merge_commit(
        repo,
        request.branch_a,
        request.branch_b,
        message=request.message,
        target_branch=target_branch,
    )
    framework = build_repository_merge_framework(
        repo, request.branch_a, request.branch_b
    )
    tree_paths = [path for path, _sha in git.iter_flat_tree_entries(commit_sha)]
    manifest_paths = _entries_under(tree_paths, _MANIFEST_ROOT)
    return MergeCommitReport(
        surface="storage_merge_commit",
        branch_a=request.branch_a,
        branch_b=request.branch_b,
        target_branch=target_branch,
        commit_sha=commit_sha,
        claims_paths=tuple(_entries_under(tree_paths, _CLAIM_ROOT)),
        manifest_path=manifest_paths[0] if manifest_paths else None,
        semantic_candidate_count=len(framework.semantic_candidates),
    )


__all__ = [
    "MergeCommitReport",
    "MergeCommitRequest",
    "commit_merge",
]

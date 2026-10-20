"""Application-layer repository merge facade (Phase 10-1).

The ``pks merge commit`` adapter needs a rich report, but the storage core
:func:`~propstore.merge.create_merge_commit` returns only the merge commit sha.
This facade calls that core and then reads the resulting tree back into a typed
:class:`MergeCommitReport` — the surviving claim blob paths, the materialized
manifest path, and the semantic-candidate count from the formal framework. It is
owner-layer (no Click / stdout / ``sys.exit``); the CLI adapter renders it.

Inspect and commit share the same captured-head target admission plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from propstore.families.claims import Claim
from propstore.families.merge_manifests import MergeManifest
from propstore.merge import build_repository_merge_framework, summarize_merge_framework
from propstore.merge.merge_classifier import RepositoryMergeFramework
from propstore.merge.merge_commit import MergeCommitPlan, plan_merge_commit
from propstore.reporting import JsonReportMixin, json_ready

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
class MergeInspectRequest:
    branch_a: str
    branch_b: str
    semantics: str = "grounded"
    target_branch: str | None = None


@dataclass(frozen=True)
class MergeInspectReport:
    plan: MergeCommitPlan
    framework: RepositoryMergeFramework
    semantics: str

    def to_json(self) -> dict[str, Any]:
        """Keep the formal query report shape, adding publication admission."""
        return {
            **summarize_merge_framework(self.framework, semantics=self.semantics),
            "plan": json_ready(self.plan),
            "target_admission": self.plan.target_admission,
        }


def inspect_merge(repo: Repository, request: MergeInspectRequest) -> MergeInspectReport:
    plan = plan_merge_commit(
        repo, request.branch_a, request.branch_b, target_branch=request.target_branch
    )
    framework = build_repository_merge_framework(
        repo, plan.branch_a, plan.branch_b, branch_commits=plan.branch_commits
    )
    return MergeInspectReport(plan, framework, request.semantics)


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
    plan: MergeCommitPlan
    target_admission: Literal["absent", "contained"]


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
    plan = plan_merge_commit(
        repo,
        request.branch_a,
        request.branch_b,
        target_branch=request.target_branch,
    )
    commit_sha = plan.commit(repo, message=request.message)
    framework = build_repository_merge_framework(
        repo, request.branch_a, request.branch_b
    )
    tree_paths = [path for path, _sha in git.iter_flat_tree_entries(commit_sha)]
    manifest_paths = _entries_under(tree_paths, _MANIFEST_ROOT)
    return MergeCommitReport(
        surface="storage_merge_commit",
        branch_a=request.branch_a,
        branch_b=request.branch_b,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        claims_paths=tuple(_entries_under(tree_paths, _CLAIM_ROOT)),
        manifest_path=manifest_paths[0] if manifest_paths else None,
        semantic_candidate_count=len(framework.semantic_candidates),
        plan=plan,
        target_admission=plan.target_admission,
    )


__all__ = [
    "MergeCommitReport",
    "MergeCommitRequest",
    "MergeInspectRequest",
    "MergeInspectReport",
    "commit_merge",
    "inspect_merge",
]

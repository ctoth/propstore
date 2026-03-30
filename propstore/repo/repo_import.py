"""Committed-snapshot repository import planning and commit helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from propstore.cli.repository import Repository
from propstore.repo.branch import branch_head, create_branch


SEMANTIC_ROOT_DIRS = (
    "claims",
    "concepts",
    "contexts",
    "forms",
    "stances",
    "worldlines",
)


@dataclass(frozen=True)
class RepoImportPlan:
    """Planned committed-snapshot import from a source repo into a destination repo."""

    source_repo: str
    source_commit: str
    target_branch: str
    repo_name: str
    writes: dict[str, bytes]
    touched_paths: list[str]
    sync_worktree_default: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoImportResult:
    """Committed repository import result."""

    surface: str
    source_repo: str
    source_commit: str
    target_branch: str
    commit_sha: str
    touched_paths: list[str]
    worktree_synced: bool


def _infer_repo_name(repo: Repository) -> str:
    root = repo.root
    if root.name == "knowledge" and root.parent.name:
        return root.parent.name
    return root.name


def _iter_semantic_paths(repo: Repository, *, commit: str) -> dict[str, bytes]:
    git = repo.git
    if git is None:
        raise ValueError("Repository must be git-backed")

    tree = git._get_tree(commit)
    if tree is None:
        return {}

    flattened: dict[str, bytes] = {}
    git._flatten_tree(tree, "", flattened)
    return {
        path: git.read_file(path, commit=commit)
        for path in sorted(flattened)
        if path.split("/", 1)[0] in SEMANTIC_ROOT_DIRS
    }


def plan_repo_import(
    destination_repo: Repository,
    source_repo_path: Path,
    *,
    target_branch: str | None = None,
) -> RepoImportPlan:
    """Plan a committed-snapshot import from a source repo into a destination repo."""

    if destination_repo.git is None:
        raise ValueError("Destination repository must be git-backed")

    source_repo = Repository.find(source_repo_path.resolve())
    if source_repo.git is None:
        raise ValueError("Source repository must be git-backed")

    source_commit = source_repo.git.head_sha()
    if source_commit is None:
        raise ValueError("Source repository has no committed HEAD")

    repo_name = _infer_repo_name(source_repo)
    selected_branch = target_branch or f"import/{repo_name}"
    writes = _iter_semantic_paths(source_repo, commit=source_commit)
    touched_paths = sorted(writes)

    return RepoImportPlan(
        source_repo=str(source_repo.root),
        source_commit=source_commit,
        target_branch=selected_branch,
        repo_name=repo_name,
        writes=writes,
        touched_paths=touched_paths,
        sync_worktree_default=(selected_branch == "master"),
    )


def commit_repo_import(
    repo: Repository,
    plan: RepoImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepoImportResult:
    """Commit a planned import onto the destination repository."""

    git = repo.git
    if git is None:
        raise ValueError("Destination repository must be git-backed")

    if sync_worktree not in {"auto", "always", "never"}:
        raise ValueError("sync_worktree must be one of: auto, always, never")

    if branch_head(git, plan.target_branch) is None and plan.target_branch != "master":
        create_branch(git, plan.target_branch)

    commit_sha = git.commit_files(
        plan.writes,
        message or f"Import {plan.repo_name} at {plan.source_commit[:12]}",
        branch=plan.target_branch,
    )

    should_sync = False
    if sync_worktree == "always":
        if plan.target_branch != "master":
            raise ValueError("Explicit worktree sync is only supported for target_branch='master'")
        should_sync = True
    elif sync_worktree == "auto":
        should_sync = plan.sync_worktree_default

    if should_sync:
        git.sync_worktree()

    return RepoImportResult(
        surface="repo_import_commit",
        source_repo=plan.source_repo,
        source_commit=plan.source_commit,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        touched_paths=list(plan.touched_paths),
        worktree_synced=should_sync,
    )

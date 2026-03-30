"""Committed-snapshot repository import planning and commit helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from propstore.cli.repository import Repository


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

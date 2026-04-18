"""Committed-snapshot repository import planning and commit helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from propstore.families.registry import (
    semantic_family_for_path,
    semantic_import_roots,
)
from propstore.storage.repository_import_normalization import (
    PlannedSemanticWrite,
    normalize_semantic_import_writes,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class RepositoryImportPlan:
    """Planned committed-snapshot import between knowledge repositories."""

    source_repository: str
    source_commit: str
    target_branch: str
    repository_name: str
    writes: dict[str, PlannedSemanticWrite]
    deletes: list[str]
    touched_paths: list[str]
    sync_worktree_default: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepositoryImportResult:
    """Committed repository import result."""

    surface: str
    source_repository: str
    source_commit: str
    target_branch: str
    commit_sha: str
    touched_paths: list[str]
    deleted_paths: list[str]
    worktree_synced: bool


def _infer_repository_name(repository: Repository) -> str:
    root = repository.root
    if root.name == "knowledge" and root.parent.name:
        return root.parent.name
    return root.name


def _iter_semantic_paths(repository: Repository, *, commit: str) -> dict[str, bytes]:
    return {
        snapshot_file.relpath: snapshot_file.content
        for snapshot_file in repository.snapshot.files(
            commit=commit,
            roots=semantic_import_roots(),
        )
    }


def plan_repository_import(
    destination_repository: Repository,
    source_repository_path: Path,
    *,
    target_branch: str | None = None,
) -> RepositoryImportPlan:
    """Plan a committed-snapshot import between knowledge repositories."""
    from propstore.repository import Repository, RepositoryNotFound

    try:
        source_repository = Repository.find(source_repository_path.resolve())
    except RepositoryNotFound as exc:
        raise ValueError("Source repository must be git-backed") from exc

    source_commit = source_repository.snapshot.head_sha()
    if source_commit is None:
        raise ValueError("Source repository has no committed HEAD")

    primary_branch = destination_repository.snapshot.primary_branch_name()
    repository_name = _infer_repository_name(source_repository)
    selected_branch = target_branch or f"import/{repository_name}"
    writes, warnings = normalize_semantic_import_writes(
        destination_repository.families.store,
        _iter_semantic_paths(source_repository, commit=source_commit),
        repository_name=repository_name,
    )

    existing_paths: set[str] = set()
    existing_branch_sha = destination_repository.snapshot.branch_head(selected_branch)
    if existing_branch_sha is not None:
        existing_paths = set(_iter_semantic_paths(destination_repository, commit=existing_branch_sha))
    deletes = sorted(existing_paths - set(writes))
    touched_paths = sorted(set(writes) | set(deletes))

    return RepositoryImportPlan(
        source_repository=str(source_repository.root),
        source_commit=source_commit,
        target_branch=selected_branch,
        repository_name=repository_name,
        writes=writes,
        deletes=deletes,
        touched_paths=touched_paths,
        sync_worktree_default=(selected_branch == primary_branch),
        warnings=warnings,
    )


def commit_repository_import(
    repository: Repository,
    plan: RepositoryImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepositoryImportResult:
    """Commit a planned import onto the destination repository."""

    if sync_worktree not in {"auto", "always", "never"}:
        raise ValueError("sync_worktree must be one of: auto, always, never")

    primary_branch = repository.snapshot.primary_branch_name()
    if repository.snapshot.branch_head(plan.target_branch) is None and plan.target_branch != primary_branch:
        repository.snapshot.ensure_branch(plan.target_branch)

    with repository.families.transact(
        message=message or f"Import {plan.repository_name} at {plan.source_commit[:12]}",
        branch=plan.target_branch,
    ) as transaction:
        for planned_write in plan.writes.values():
            transaction.by_artifact_family(cast(Any, planned_write.family)).save(
                cast(Any, planned_write.ref),
                cast(Any, planned_write.document),
            )
        for path in plan.deletes:
            semantic_family = semantic_family_for_path(path)
            bound_family = transaction.by_artifact_family(cast(Any, semantic_family.artifact_family))
            bound_family.delete(bound_family.ref_from_path(path))
    commit_sha = transaction.commit_sha
    if commit_sha is None:
        raise ValueError("repo import transaction did not produce a commit")

    should_sync = False
    if sync_worktree == "always":
        if plan.target_branch != primary_branch:
            raise ValueError(
                "Explicit worktree sync is only supported for the primary branch"
            )
        should_sync = True
    elif sync_worktree == "auto":
        should_sync = plan.sync_worktree_default

    if should_sync:
        repository.snapshot.sync_worktree()

    return RepositoryImportResult(
        surface="repository_import_commit",
        source_repository=plan.source_repository,
        source_commit=plan.source_commit,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        touched_paths=list(plan.touched_paths),
        deleted_paths=list(plan.deletes),
        worktree_synced=should_sync,
    )

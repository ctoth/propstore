from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, TypeVar

from quire.documents import decode_document_bytes
from quire.git_store import MaterializeConflictError
from propstore.families.registry import semantic_init_roots
from propstore.storage import PROPSTORE_GIT_POLICY

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

TDocument = TypeVar("TDocument")


@dataclass(frozen=True)
class BranchInfo:
    name: str
    tip_sha: str
    kind: str
    parent_branch: str = ""
    created_at: int = 0


@dataclass(frozen=True)
class MaterializeReport:
    source_commit: str
    written_paths: tuple[str, ...]
    deleted_stale_paths: tuple[str, ...]
    skipped_ignored_paths: tuple[str, ...]
    clean: bool
    force: bool


def _branch_kind(name: str) -> str:
    for prefix in ("paper/", "source/", "agent/", "hypothesis/"):
        if name.startswith(prefix):
            return prefix.rstrip("/")
    return "workspace"


class RepositorySnapshot:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    @property
    def repo(self) -> Repository:
        return self._repo

    @property
    def git(self) -> GitStore:
        git = self._repo.git
        if git is None:
            raise ValueError("snapshot operations require a git-backed repository")
        return git

    def iter_branches(self) -> Iterator[BranchInfo]:
        for branch in self.git.iter_branches():
            yield BranchInfo(
                name=branch.name,
                tip_sha=branch.tip_sha,
                kind=_branch_kind(branch.name),
                parent_branch=branch.parent_branch,
                created_at=branch.created_at,
            )

    def tree(self, commit: str | None = None):
        return self._repo.tree(commit=commit)

    def read_document(
        self,
        relpath: str | Path,
        document_type: type[TDocument],
        *,
        branch: str | None = None,
        commit: str | None = None,
    ) -> TDocument | None:
        target_commit = commit
        source_label = str(relpath).replace("\\", "/")
        if target_commit is None:
            branch_name = branch
            if branch_name is None:
                branch_name = self.git.current_branch_name() or self.git.primary_branch_name()
            target_commit = self.git.branch_sha(branch_name)
            if target_commit is None:
                return None
            source_label = f"{branch_name}:{source_label}"
        else:
            source_label = f"{target_commit}:{source_label}"
        try:
            payload = self.git.read_file(relpath, commit=target_commit)
        except FileNotFoundError:
            return None
        return decode_document_bytes(payload, document_type, source=source_label)

    def materialize(
        self,
        *,
        commit: str | None = None,
        branch: str | None = None,
        clean: bool = False,
        force: bool = False,
    ) -> MaterializeReport:
        if commit is not None and branch is not None:
            raise ValueError("materialize accepts either commit or branch, not both")
        git = self.git
        source_commit = commit
        materialize_branch = branch
        if source_commit is None and materialize_branch is None:
            materialize_branch = git.current_branch_name() or git.primary_branch_name()
        if branch is not None:
            source_commit = git.branch_sha(branch)
            if source_commit is None:
                raise ValueError(f"Branch {branch!r} has no commit")
        elif materialize_branch is not None:
            source_commit = git.branch_sha(materialize_branch)
        if source_commit is None:
            source_commit = git.head_sha()

        clean_roots = tuple(semantic_init_roots())
        tracked_paths = (
            {tree_file.relpath for tree_file in git.iter_tree_files(commit=source_commit)}
            if clean and source_commit is not None
            else set()
        )
        quire_report = git.materialize(
            root=self.repo.root,
            commit=commit,
            branch=materialize_branch,
            clean=clean,
            clean_roots=clean_roots,
            ignored_path=PROPSTORE_GIT_POLICY.ignores_path,
            force=force,
        )
        skipped_ignored = (
            _ignored_clean_paths(self.repo.root, clean_roots=clean_roots, tracked_paths=tracked_paths)
            if clean
            else ()
        )
        return MaterializeReport(
            source_commit=source_commit or "",
            written_paths=quire_report.written_paths,
            deleted_stale_paths=quire_report.deleted_paths,
            skipped_ignored_paths=skipped_ignored,
            clean=clean,
            force=force,
        )


def _ignored_clean_paths(
    root: Path,
    *,
    clean_roots: tuple[str, ...],
    tracked_paths: set[str],
) -> tuple[str, ...]:
    skipped: list[str] = []
    for clean_root in clean_roots:
        search_root = root / clean_root
        if not search_root.exists():
            continue
        for disk_file in search_root.rglob("*"):
            if not disk_file.is_file():
                continue
            relpath = disk_file.relative_to(root).as_posix()
            if relpath in tracked_paths:
                continue
            if PROPSTORE_GIT_POLICY.ignores_path(relpath):
                skipped.append(relpath)
    return tuple(sorted(skipped))

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, TypeVar

from quire.documents import decode_document_bytes
from propstore.families.registry import semantic_init_roots
from propstore.storage.git_policy import _is_ignored_runtime_path

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

TDocument = TypeVar("TDocument")


@dataclass(frozen=True)
class SnapshotDirEntry:
    name: str
    relpath: str
    is_dir: bool


@dataclass(frozen=True)
class SnapshotFile:
    relpath: str
    content: bytes


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


class MaterializeConflictError(Exception):
    pass


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

    def primary_branch_name(self) -> str:
        return self.git.primary_branch_name()

    def current_branch_name(self) -> str | None:
        return self.git.current_branch_name()

    def head_sha(self) -> str | None:
        return self.git.head_sha()

    def branch_head(self, name: str) -> str | None:
        return self.git.branch_sha(name)

    def ensure_branch(self, name: str, *, source_commit: str | None = None) -> str:
        tip = self.branch_head(name)
        if tip is not None:
            return tip
        return self.git.create_branch(name, source_commit=source_commit)

    def delete_branch(self, name: str) -> None:
        self.git.delete_branch(name)

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

    def read_bytes(self, relpath: str | Path, *, commit: str) -> bytes:
        return self.git.read_file(relpath, commit=commit)

    def read_text(self, relpath: str | Path, *, commit: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(relpath, commit=commit).decode(encoding)

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
                branch_name = self.current_branch_name() or self.primary_branch_name()
            target_commit = self.branch_head(branch_name)
            if target_commit is None:
                return None
            source_label = f"{branch_name}:{source_label}"
        else:
            source_label = f"{target_commit}:{source_label}"
        try:
            payload = self.read_bytes(relpath, commit=target_commit)
        except FileNotFoundError:
            return None
        return decode_document_bytes(payload, document_type, source=source_label)

    def iter_dir(self, subdir: str | Path, *, commit: str | None = None) -> Iterator[str]:
        return self.git.iter_dir(subdir, commit=commit)

    def iter_dir_entries(self, subdir: str | Path, *, commit: str | None = None) -> Iterator[SnapshotDirEntry]:
        prefix = str(subdir).replace("\\", "/").strip("/")
        for name, is_dir in self.git.iter_dir_entries(subdir, commit=commit):
            relpath = f"{prefix}/{name}" if prefix else name
            yield SnapshotDirEntry(name=name, relpath=relpath, is_dir=is_dir)

    def files(
        self,
        *,
        commit: str,
        roots: tuple[str, ...] | None = None,
    ) -> list[SnapshotFile]:
        tree = self.tree(commit=commit)
        files: list[SnapshotFile] = []

        def collect(node) -> None:
            if node.is_file():
                files.append(SnapshotFile(relpath=node.as_posix(), content=node.read_bytes()))
                return
            if not node.is_dir():
                return
            for child in node.iterdir():
                collect(child)

        if roots is None:
            collect(tree)
        else:
            for root_name in roots:
                root = tree / root_name
                if root.exists():
                    collect(root)

        files.sort(key=lambda snapshot_file: snapshot_file.relpath)
        return files

    def sync_worktree(self) -> None:
        self.git.sync_worktree()

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
        head_txn = None
        if commit is None:
            branch_name = branch or self.current_branch_name() or self.primary_branch_name()
            head_txn = self.repo.head_bound_transaction(branch_name, path="materialize")

        with head_txn if head_txn is not None else nullcontext():
            if commit is None:
                if head_txn is None:
                    raise ValueError("materialize requires a commit or captured branch head")
                commit = head_txn.expected_head
                if commit is None:
                    raise ValueError(f"Branch {branch_name!r} has no commit")

            snapshot_files = self.files(commit=commit)
            if head_txn is not None:
                head_txn.assert_current()
            tracked_paths = {snapshot_file.relpath for snapshot_file in snapshot_files}
            conflicts: list[str] = []
            written: list[str] = []
            for snapshot_file in snapshot_files:
                destination = self.repo.root / snapshot_file.relpath
                if destination.exists() and destination.is_file():
                    existing = destination.read_bytes()
                    if existing != snapshot_file.content and not force:
                        conflicts.append(snapshot_file.relpath)
                        continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(snapshot_file.content)
                written.append(snapshot_file.relpath)

            if conflicts:
                details = ", ".join(sorted(conflicts))
                raise MaterializeConflictError(f"Refusing to overwrite local edits: {details}")

            deleted, skipped = self._clean_materialized_semantic_files(tracked_paths) if clean else ([], [])
            return MaterializeReport(
                source_commit=commit,
                written_paths=tuple(sorted(written)),
                deleted_stale_paths=tuple(sorted(deleted)),
                skipped_ignored_paths=tuple(sorted(skipped)),
                clean=clean,
                force=force,
            )

    def _clean_materialized_semantic_files(self, tracked_paths: set[str]) -> tuple[list[str], list[str]]:
        semantic_roots = tuple(f"{root}/" for root in semantic_init_roots())
        deleted: list[str] = []
        skipped: list[str] = []
        prune_candidates: set[Path] = set()
        for disk_file in self.repo.root.rglob("*"):
            if not disk_file.is_file():
                continue
            relpath = disk_file.relative_to(self.repo.root).as_posix()
            if relpath.startswith(".git/") or relpath == ".git":
                continue
            if not relpath.startswith(semantic_roots):
                continue
            if relpath in tracked_paths:
                continue
            if _is_ignored_runtime_path(relpath):
                skipped.append(relpath)
                continue
            disk_file.unlink()
            deleted.append(relpath)
            parent = disk_file.parent
            while parent != self.repo.root:
                prune_candidates.add(parent)
                parent = parent.parent
        for directory in sorted(
            prune_candidates,
            key=lambda path: len(path.relative_to(self.repo.root).parts),
            reverse=True,
        ):
            relpath = directory.relative_to(self.repo.root).as_posix()
            if relpath.startswith(".git/") or relpath == ".git":
                continue
            if _is_ignored_runtime_path(relpath):
                continue
            try:
                directory.rmdir()
            except OSError:
                continue
        return deleted, skipped

    def log(self, *, max_count: int = 50, branch: str | None = None) -> list[dict]:
        return self.git.log(max_count=max_count, branch=branch)

    def show_commit(self, sha: str) -> dict:
        return self.git.show_commit(sha)

    def diff(self, commit1: str | None = None, commit2: str | None = None) -> dict:
        return self.git.diff_commits(commit1, commit2)

    def merge_base(self, branch_a: str, branch_b: str) -> str:
        return self.git.merge_base(branch_a, branch_b)

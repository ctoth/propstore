from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, TypeVar

from quire.documents import decode_document_bytes
from propstore.families.registry import semantic_init_roots
from propstore.storage import PROPSTORE_GIT_POLICY

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

TDocument = TypeVar("TDocument")


@dataclass(frozen=True)
class SnapshotFile:
    relpath: str
    content: bytes


@dataclass(frozen=True)
class _MaterializeWrite:
    relpath: str
    destination: Path
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


def _is_propstore_ignored_runtime_path(relpath: str) -> bool:
    normalized = relpath.replace("\\", "/")
    return normalized.startswith(PROPSTORE_GIT_POLICY.ignored_path_prefixes) or normalized.endswith(
        PROPSTORE_GIT_POLICY.ignored_path_suffixes
    )


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

    def _files(
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
            branch_name = branch or self.git.current_branch_name() or self.git.primary_branch_name()
            head_txn = self.git.head_bound_transaction(branch_name)

        with head_txn if head_txn is not None else nullcontext():
            if commit is None:
                if head_txn is None:
                    raise ValueError("materialize requires a commit or captured branch head")
                commit = head_txn.expected_head
                if commit is None:
                    raise ValueError(f"Branch {branch_name!r} has no commit")

            snapshot_files = self._files(commit=commit)
            if head_txn is not None:
                head_txn.assert_current()
            tracked_paths = {snapshot_file.relpath for snapshot_file in snapshot_files}
            conflicts: list[str] = []
            writes: list[_MaterializeWrite] = []
            for snapshot_file in snapshot_files:
                destination = self.repo.root / snapshot_file.relpath
                if destination.exists() and destination.is_file():
                    existing = destination.read_bytes()
                    if existing != snapshot_file.content and not force:
                        conflicts.append(snapshot_file.relpath)
                        continue
                    if existing == snapshot_file.content:
                        continue
                writes.append(
                    _MaterializeWrite(
                        relpath=snapshot_file.relpath,
                        destination=destination,
                        content=snapshot_file.content,
                    )
                )

            if conflicts:
                details = ", ".join(sorted(conflicts))
                raise MaterializeConflictError(f"Refusing to overwrite local edits: {details}")

            written: list[str] = []
            for write in writes:
                write.destination.parent.mkdir(parents=True, exist_ok=True)
                write.destination.write_bytes(write.content)
                written.append(write.relpath)

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
        deletion_candidates: list[tuple[Path, str]] = []
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
            if _is_propstore_ignored_runtime_path(relpath):
                skipped.append(relpath)
                continue
            deletion_candidates.append((disk_file, relpath))
        for disk_file, relpath in deletion_candidates:
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
            if _is_propstore_ignored_runtime_path(relpath):
                continue
            try:
                directory.rmdir()
            except OSError:
                continue
        return deleted, skipped

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeVar

from propstore.document_schema import decode_document_bytes
from propstore.repo.branch import BranchInfo, branch_head, create_branch, delete_branch, list_branches, merge_base

if TYPE_CHECKING:
    from propstore.cli.repository import Repository
    from propstore.repo.git_backend import KnowledgeRepo

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


class RepoSnapshot:
    @classmethod
    def for_git(cls, git: object) -> RepoSnapshot:
        return cls(SimpleNamespace(git=git, tree=lambda commit=None: git.tree(commit=commit)))

    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    @property
    def repo(self) -> Repository:
        return self._repo

    @property
    def git(self) -> KnowledgeRepo:
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
        return branch_head(self.git, name)

    def next_concept_id(self) -> int:
        return self.git.next_concept_id()

    def ensure_branch(self, name: str, *, source_commit: str | None = None) -> str:
        tip = self.branch_head(name)
        if tip is not None:
            return tip
        return create_branch(self.git, name, source_commit=source_commit)

    def delete_branch(self, name: str) -> None:
        delete_branch(self.git, name)

    def list_branches(self) -> list[BranchInfo]:
        return list_branches(self.git)

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

    def list_dir(self, subdir: str | Path, *, commit: str | None = None) -> list[str]:
        return self.git.list_dir(subdir, commit=commit)

    def list_dir_entries(self, subdir: str | Path, *, commit: str | None = None) -> list[SnapshotDirEntry]:
        prefix = str(subdir).replace("\\", "/").strip("/")
        entries: list[SnapshotDirEntry] = []
        for name, is_dir in self.git.list_dir_entries(subdir, commit=commit):
            relpath = f"{prefix}/{name}" if prefix else name
            entries.append(SnapshotDirEntry(name=name, relpath=relpath, is_dir=is_dir))
        return entries

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

    def log(self, *, max_count: int = 50, branch: str | None = None) -> list[dict]:
        return self.git.log(max_count=max_count, branch=branch)

    def show_commit(self, sha: str) -> dict:
        return self.git.show_commit(sha)

    def diff(self, commit1: str | None = None, commit2: str | None = None) -> dict:
        return self.git.diff_commits(commit1, commit2)

    def merge_base(self, branch_a: str, branch_b: str) -> str:
        return merge_base(self.git, branch_a, branch_b)

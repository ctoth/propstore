"""Propstore policy wrapper around quire's typed git store."""
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from dulwich.repo import BaseRepo, MemoryRepo, Repo
from quire.git_store import (
    GitStore as QuireGitStore,
    GitStorePolicy,
    _commit_object,
    _ref_delete,
    _ref_get,
    _ref_set,
    _set_symbolic_ref,
)

_DEFAULT_AUTHOR = b"pks <pks@propstore>"
_PRIMARY_BRANCH = "master"
_GITIGNORE_CONTENT = """\
sidecar/
*.sqlite
*.sqlite-wal
*.sqlite-shm
*.hash
*.provenance
"""

_PROPSTORE_POLICY = GitStorePolicy(
    author=_DEFAULT_AUTHOR,
    primary_branch=_PRIMARY_BRANCH,
    initial_files={".gitignore": _GITIGNORE_CONTENT.encode("utf-8")},
    initial_commit_message="Initialize knowledge repository",
    ignored_path_prefixes=("sidecar/",),
    ignored_path_suffixes=(
        ".sqlite",
        ".sqlite-wal",
        ".sqlite-shm",
        ".hash",
        ".provenance",
    ),
)


def _is_ignored_runtime_path(relpath: str) -> bool:
    normalized = relpath.replace("\\", "/")
    return normalized.startswith(_PROPSTORE_POLICY.ignored_path_prefixes) or normalized.endswith(
        _PROPSTORE_POLICY.ignored_path_suffixes
    )


def _walker(repo: Any, tip: bytes, *, max_entries: int) -> Any:
    return repo.get_walker(include=[tip], max_entries=max_entries)


class GitStore(QuireGitStore):
    """Git-backed knowledge repository with propstore defaults."""

    def __init__(
        self,
        dulwich_repo: BaseRepo,
        root: Path | None = None,
        *,
        policy: GitStorePolicy | None = None,
    ) -> None:
        super().__init__(dulwich_repo, root, policy=policy or _PROPSTORE_POLICY)

    @classmethod
    def init(cls, root: Path) -> GitStore:
        root.mkdir(parents=True, exist_ok=True)
        store = cls(Repo.init(str(root)), root)
        store.commit_files(
            cast("dict[str | Path, bytes]", dict(_PROPSTORE_POLICY.initial_files)),
            _PROPSTORE_POLICY.initial_commit_message,
        )
        store.sync_worktree()
        return store

    @classmethod
    def init_memory(cls) -> GitStore:
        store = cls(MemoryRepo())
        store.commit_files(
            cast("dict[str | Path, bytes]", dict(_PROPSTORE_POLICY.initial_files)),
            _PROPSTORE_POLICY.initial_commit_message,
        )
        return store

    @classmethod
    def open(cls, root: Path) -> GitStore:
        return cls(Repo(str(root)), root)

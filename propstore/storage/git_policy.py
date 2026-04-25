"""Propstore git-store policy."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from quire.git_store import GitStore, GitStorePolicy

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


def init_git_store(root: Path) -> GitStore:
    return GitStore.init(root, policy=_PROPSTORE_POLICY)


def init_memory_git_store() -> GitStore:
    return GitStore.init_memory(policy=_PROPSTORE_POLICY)


def open_git_store(root: Path) -> GitStore:
    return GitStore.open(root, policy=_PROPSTORE_POLICY)


def is_git_repo(root: Path) -> bool:
    return GitStore.is_repo(root)

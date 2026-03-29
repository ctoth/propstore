"""TreeReader protocol and implementations for reading YAML from knowledge trees.

Abstracts over "read YAML files from a directory" so that loaders and build
can read from either the filesystem or a git object store.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from propstore.repo.git_backend import KnowledgeRepo


class TreeReader(Protocol):
    """Read-only interface over a tree of YAML files."""

    def list_yaml(self, subdir: str) -> list[tuple[str, bytes]]:
        """Return (stem, raw_bytes) for every .yaml file in *subdir*, sorted by stem."""
        ...

    def read_yaml(self, path: str) -> bytes | None:
        """Read a single file by repo-relative posix path. Returns None if missing."""
        ...

    def exists(self, subdir: str) -> bool:
        """Return True if *subdir* exists and contains at least one entry."""
        ...


class FilesystemReader:
    """TreeReader backed by the local filesystem."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def list_yaml(self, subdir: str) -> list[tuple[str, bytes]]:
        d = self._root / subdir
        if not d.is_dir():
            return []
        results: list[tuple[str, bytes]] = []
        for entry in sorted(d.iterdir()):
            if entry.is_file() and entry.suffix == ".yaml":
                results.append((entry.stem, entry.read_bytes()))
        return results

    def read_yaml(self, path: str) -> bytes | None:
        p = self._root / path
        if p.is_file():
            return p.read_bytes()
        return None

    def exists(self, subdir: str) -> bool:
        return (self._root / subdir).is_dir()


class GitTreeReader:
    """TreeReader backed by a Dulwich git object store."""

    def __init__(self, repo: KnowledgeRepo, commit: str | None = None) -> None:
        self._repo = repo
        self._commit = commit

    def list_yaml(self, subdir: str) -> list[tuple[str, bytes]]:
        try:
            names = self._repo.list_dir(subdir, commit=self._commit)
        except (FileNotFoundError, KeyError):
            return []
        results: list[tuple[str, bytes]] = []
        for name in sorted(names):
            if name.endswith(".yaml"):
                stem = name[:-5]  # strip .yaml
                content = self._repo.read_file(f"{subdir}/{name}", commit=self._commit)
                results.append((stem, content))
        return results

    def read_yaml(self, path: str) -> bytes | None:
        try:
            return self._repo.read_file(path, commit=self._commit)
        except (FileNotFoundError, KeyError):
            return None

    def exists(self, subdir: str) -> bool:
        try:
            entries = self._repo.list_dir(subdir, commit=self._commit)
            return len(entries) > 0
        except (FileNotFoundError, KeyError):
            return False

"""Repository — locates and provides paths within a propstore knowledge/ directory."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

import yaml

from propstore.knowledge_path import FilesystemKnowledgePath, GitKnowledgePath, KnowledgePath
from propstore.uri import DEFAULT_URI_AUTHORITY


class RepositoryNotFound(Exception):
    """Raised when no knowledge/ directory can be found."""


class Repository:
    """A propstore knowledge repository rooted at a ``knowledge/`` directory.

    All path resolution for concepts, claims, forms, sidecar, and counters
    goes through this object.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    @property
    def concepts_dir(self) -> Path:
        return self._root / "concepts"

    @property
    def claims_dir(self) -> Path:
        return self._root / "claims"

    @property
    def forms_dir(self) -> Path:
        return self._root / "forms"

    @property
    def sidecar_dir(self) -> Path:
        return self._root / "sidecar"

    @property
    def sidecar_path(self) -> Path:
        return self._root / "sidecar" / "propstore.sqlite"

    @property
    def contexts_dir(self) -> Path:
        return self._root / "contexts"

    @property
    def stances_dir(self) -> Path:
        return self._root / "stances"

    @property
    def justifications_dir(self) -> Path:
        return self._root / "justifications"

    @property
    def sources_dir(self) -> Path:
        return self._root / "sources"

    @property
    def worldlines_dir(self) -> Path:
        return self._root / "worldlines"

    @property
    def config_path(self) -> Path:
        return self._root / "propstore.yaml"

    @cached_property
    def config(self) -> dict:
        if not self.config_path.exists():
            return {}
        loaded = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}

    @property
    def uri_authority(self) -> str:
        authority = self.config.get("uri_authority")
        if isinstance(authority, str) and authority:
            return authority
        return DEFAULT_URI_AUTHORITY

    @property
    def counters_dir(self) -> Path:
        return self._root / "concepts" / ".counters"

    def tree(self, commit: str | None = None) -> KnowledgePath:
        """Return a read-only semantic tree rooted at this repository."""
        if self.git is None:
            if commit is not None:
                raise ValueError("Repository.tree(commit=...) requires a git-backed repository")
            return FilesystemKnowledgePath.from_filesystem_path(self._root)
        return GitKnowledgePath(self.git, commit=commit)

    @cached_property
    def git(self):
        """Return the KnowledgeRepo if this directory is git-backed, else None."""
        from propstore.repo import KnowledgeRepo
        if KnowledgeRepo.is_repo(self._root):
            return KnowledgeRepo.open(self._root)
        return None

    @cached_property
    def store(self):
        from propstore.world import WorldModel

        return WorldModel(self)

    def close(self) -> None:
        store = self.__dict__.get("store")
        if store is not None:
            store.close()

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root if it contains
        a ``concepts/`` subdirectory (e.g. ``pks -C path/to/knowledge``
        or when cwd is already inside the knowledge tree).
        """
        from propstore.repo import KnowledgeRepo

        current = (start or Path.cwd()).resolve()
        # If start itself has the knowledge structure (e.g. -C pointed at it,
        # or cwd is already the knowledge dir)
        if (current / "concepts").is_dir():
            if KnowledgeRepo.is_repo(current):
                return cls(current)
            raise RepositoryNotFound(
                f"No git-backed knowledge/ directory found (searched from {current}). "
                f"Run 'pks init' to create one."
            )
        # Walk up looking for knowledge/
        for ancestor in [current, *current.parents]:
            candidate = ancestor / "knowledge"
            if candidate.is_dir() and (candidate / "concepts").is_dir():
                if KnowledgeRepo.is_repo(candidate):
                    return cls(candidate)
        raise RepositoryNotFound(
            f"No git-backed knowledge/ directory found (searched from {current}). "
            f"Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create the directory structure and return a Repository."""
        # Initialize git first (sync_worktree in init only writes .gitignore)
        from propstore.repo import KnowledgeRepo
        KnowledgeRepo.init(root)
        # Create dirs after git init so sync_worktree doesn't remove them
        dirs = [
            root / "concepts" / ".counters",
            root / "claims",
            root / "contexts",
            root / "forms",
            root / "justifications",
            root / "sidecar",
            root / "sources",
            root / "stances",
            root / "worldlines",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return cls(root)

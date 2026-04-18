"""Repository — locates and provides paths within a propstore knowledge/ directory."""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

from quire.documents import DocumentStruct, decode_document_bytes
from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, GitTreePath as GitKnowledgePath, TreePath as KnowledgePath
from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES
from propstore.uri import DEFAULT_URI_AUTHORITY


class RepositoryNotFound(Exception):
    """Raised when no knowledge/ directory can be found."""


class RepositoryConfigDocument(DocumentStruct):
    uri_authority: str | None = None


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
        return SEMANTIC_FAMILIES.root_path("concept", self)

    @property
    def claims_dir(self) -> Path:
        return SEMANTIC_FAMILIES.root_path("claim", self)

    @property
    def forms_dir(self) -> Path:
        return SEMANTIC_FAMILIES.root_path("form", self)

    @property
    def sidecar_dir(self) -> Path:
        return self._root / "sidecar"

    @property
    def sidecar_path(self) -> Path:
        return self._root / "sidecar" / "propstore.sqlite"

    @property
    def contexts_dir(self) -> Path:
        return SEMANTIC_FAMILIES.root_path("context", self)

    @property
    def stances_dir(self) -> Path:
        return SEMANTIC_FAMILIES.root_path("stance", self)

    @property
    def justifications_dir(self) -> Path:
        return self._root / "justifications"

    @property
    def sources_dir(self) -> Path:
        return self._root / "sources"

    @property
    def worldlines_dir(self) -> Path:
        return SEMANTIC_FAMILIES.root_path("worldline", self)

    @property
    def config_path(self) -> Path:
        return self._root / "propstore.yaml"

    @cached_property
    def config(self) -> dict:
        if not self.config_path.exists():
            return {}
        loaded = decode_document_bytes(
            self.config_path.read_bytes(),
            RepositoryConfigDocument,
            source=str(self.config_path),
        )
        config: dict[str, str] = {}
        if loaded.uri_authority is not None:
            config["uri_authority"] = loaded.uri_authority
        return config

    @property
    def uri_authority(self) -> str:
        authority = self.config.get("uri_authority")
        if isinstance(authority, str) and authority:
            return authority
        return DEFAULT_URI_AUTHORITY

    @property
    def counters_dir(self) -> Path:
        return self.concepts_dir / ".counters"

    def tree(self, commit: str | None = None) -> KnowledgePath:
        """Return a read-only semantic tree rooted at this repository."""
        if self.git is None:
            if commit is not None:
                raise ValueError("Repository.tree(commit=...) requires a git-backed repository")
            return FilesystemKnowledgePath.from_filesystem_path(self._root)
        return GitKnowledgePath(self.git, commit=commit)

    @cached_property
    def git(self):
        """Return the GitStore if this directory is git-backed, else None."""
        from propstore.storage import is_git_repo, open_git_store
        if is_git_repo(self._root):
            return open_git_store(self._root)
        return None

    @cached_property
    def artifacts(self):
        from propstore.artifacts.policy import create_artifact_store

        return create_artifact_store(self)

    @cached_property
    def families(self):
        from propstore.artifacts.families import PROPSTORE_FAMILY_REGISTRY

        return PROPSTORE_FAMILY_REGISTRY.bind(self, self.artifacts)

    @cached_property
    def snapshot(self):
        from propstore.storage.snapshot import RepositorySnapshot

        return RepositorySnapshot(self)

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root if it contains
        a ``concepts/`` subdirectory (e.g. ``pks -C path/to/knowledge``
        or when cwd is already inside the knowledge tree).
        """
        from propstore.storage import is_git_repo

        current = (start or Path.cwd()).resolve()
        # If start itself has the knowledge structure (e.g. -C pointed at it,
        # or cwd is already the knowledge dir)
        if SEMANTIC_FAMILIES.root_path("concept", current).is_dir():
            if is_git_repo(current):
                return cls(current)
            raise RepositoryNotFound(
                f"No git-backed knowledge/ directory found (searched from {current}). "
                f"Run 'pks init' to create one."
            )
        # Walk up looking for knowledge/
        for ancestor in [current, *current.parents]:
            candidate = ancestor / "knowledge"
            if candidate.is_dir() and SEMANTIC_FAMILIES.root_path("concept", candidate).is_dir():
                if is_git_repo(candidate):
                    return cls(candidate)
        raise RepositoryNotFound(
            f"No git-backed knowledge/ directory found (searched from {current}). "
            f"Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create the directory structure and return a Repository."""
        # Initialize git first (sync_worktree in init only writes .gitignore)
        from propstore.storage import init_git_store

        init_git_store(root)
        # Create dirs after git init so sync_worktree doesn't remove them
        repo = cls(root)
        dirs = [
            SEMANTIC_FAMILIES.root_path(name, repo)
            for name in SEMANTIC_FAMILIES.names()
            if SEMANTIC_FAMILIES.by_name(name).init_directory
        ]
        dirs.extend([
            repo.concepts_dir / ".counters",
            root / "justifications",
            root / "sidecar",
            root / "sources",
        ])
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return repo

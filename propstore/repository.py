"""Repository — locates and provides paths within a propstore knowledge/ directory."""
from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

from quire.documents import DocumentStruct, decode_document_bytes
from quire.refs import RefName
from quire.tree_path import FilesystemTreePath as FilesystemKnowledgePath, GitTreePath as GitKnowledgePath, TreePath as KnowledgePath
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
)
from propstore.uri import DEFAULT_URI_AUTHORITY
from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

PROPSTORE_BOOTSTRAP_REF = RefName("refs/propstore/bootstrap")
PROPSTORE_REPOSITORY_FORMAT_VERSION = "2026.04.store-only-init"
REPOSITORY_CONFIG_PATH = "propstore.yaml"


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
    def sidecar_dir(self) -> Path:
        return self._root / "sidecar"

    @property
    def sidecar_path(self) -> Path:
        return self._root / "sidecar" / "propstore.sqlite"

    @cached_property
    def config(self) -> dict[str, TaggingAuthority]:
        if self.git is None:
            return {}
        try:
            payload = self.git.read_file(REPOSITORY_CONFIG_PATH)
        except FileNotFoundError:
            return {}
        loaded = decode_document_bytes(
            payload,
            RepositoryConfigDocument,
            source=REPOSITORY_CONFIG_PATH,
        )
        config: dict[str, TaggingAuthority] = {}
        if loaded.uri_authority is not None:
            config["uri_authority"] = parse_tagging_authority(loaded.uri_authority)
        return config

    @property
    def uri_authority(self) -> TaggingAuthority:
        authority = self.config.get("uri_authority")
        if isinstance(authority, TaggingAuthority):
            return authority
        return DEFAULT_URI_AUTHORITY

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
    def _family_store(self):
        from quire.family_store import DocumentFamilyStore

        return DocumentFamilyStore(
            owner=self,
            backend=self.git,
        )

    @cached_property
    def families(self):
        from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY

        return PROPSTORE_FAMILY_REGISTRY.bind(self, self._family_store)

    @cached_property
    def snapshot(self):
        from propstore.storage.snapshot import RepositorySnapshot

        return RepositorySnapshot(self)

    @classmethod
    def is_propstore_repo(cls, root: Path) -> bool:
        """Return whether *root* is a git store with propstore bootstrap state."""
        from propstore.storage import is_git_repo, open_git_store

        if not is_git_repo(root):
            return False
        return _read_bootstrap_manifest(open_git_store(root)) is not None

    def write_bootstrap_manifest(self, *, seed_commit: str | None = None) -> None:
        _write_bootstrap_manifest(self.git, seed_commit=seed_commit)

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root when it is a
        git-backed propstore store.
        """
        from propstore.storage import is_git_repo

        current = (start or Path.cwd()).resolve()
        if is_git_repo(current):
            if cls.is_propstore_repo(current):
                return cls(current)
            raise RepositoryNotFound(
                f"Git repository at {current} is not a propstore repository. "
                f"Run 'pks init' to create one."
            )
        # Walk up looking for knowledge/
        for ancestor in [current, *current.parents]:
            candidate = ancestor / "knowledge"
            if not candidate.is_dir():
                continue
            if not is_git_repo(candidate):
                continue
            if cls.is_propstore_repo(candidate):
                return cls(candidate)
            raise RepositoryNotFound(
                f"Git repository at {candidate} is not a propstore repository. "
                f"Run 'pks init' to create one."
            )
        raise RepositoryNotFound(
            f"No git-backed knowledge/ directory found (searched from {current}). "
            f"Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create a store-only propstore repository and return it."""
        from propstore.storage import init_git_store

        init_git_store(root)
        repo = cls(root)
        repo.write_bootstrap_manifest()
        return repo


def _bootstrap_manifest(seed_commit: str | None) -> dict[str, object]:
    return {
        "repository_format_version": PROPSTORE_REPOSITORY_FORMAT_VERSION,
        "family_registry_contract_version": str(PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION),
        "seed_bundle_version": "packaged-defaults",
        "seed_commit": seed_commit,
        "primary_branch": "master",
    }


def _write_bootstrap_manifest(git, *, seed_commit: str | None) -> None:
    payload = json.dumps(
        _bootstrap_manifest(seed_commit),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    git.write_blob_ref(PROPSTORE_BOOTSTRAP_REF, payload)


def _read_bootstrap_manifest(git) -> dict[str, object] | None:
    payload = git.read_blob_ref(PROPSTORE_BOOTSTRAP_REF)
    if payload is None:
        return None
    try:
        loaded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(loaded, dict):
        return None
    if loaded.get("repository_format_version") != PROPSTORE_REPOSITORY_FORMAT_VERSION:
        return None
    return loaded

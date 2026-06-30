"""Repository — the propstore knowledge repository facade.

A :class:`Repository` roots at a git-backed ``knowledge/`` directory and is the
one canonical handle onto everything beneath the render layer: the git store
(``git`` / ``require_git``), the bound family registry (``families`` — the
source-of-truth multi-family storage surface), the branch/materialize snapshot
(``snapshot``), the content-addressed derived stores, and the repository config
(``uri_authority``). It composes quire directly; nothing here re-implements a
store, a registry, or a placement.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path

import msgspec

from quire.derived_store import DerivedStoreManager
from quire.documents import DocumentStruct, decode_document_bytes
from quire.families import BoundFamilyRegistry
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.refs import RefName
from quire.tree_path import (
    FilesystemTreePath,
    GitTreePath,
    TreePath,
)

from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
)
from propstore.storage.git_policy import PROPSTORE_GIT_POLICY
from propstore.storage.snapshot import RepositorySnapshot
from propstore.uri import DEFAULT_URI_AUTHORITY
from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

PROPSTORE_BOOTSTRAP_REF = RefName("refs/propstore/bootstrap")
PROPSTORE_REPOSITORY_FORMAT_VERSION = "2026.04.store-only-init"
REPOSITORY_CONFIG_PATH = "propstore.yaml"


class RepositoryNotFound(Exception):
    """Raised when no propstore knowledge repository can be found."""


class RepositoryConfigDocument(DocumentStruct):
    uri_authority: str | None = None


class Repository:
    """A propstore knowledge repository rooted at a git-backed directory."""

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    @cached_property
    def derived_stores(self) -> DerivedStoreManager:
        return DerivedStoreManager(self._root / ".propstore" / "derived-stores")

    @cached_property
    def config(self) -> dict[str, TaggingAuthority]:
        git = self.git
        if git is None:
            return {}
        try:
            payload = git.read_file(REPOSITORY_CONFIG_PATH)
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

    def tree(self, commit: str | None = None) -> TreePath:
        """Return a read-only semantic tree rooted at this repository."""

        git = self.git
        if git is None:
            if commit is not None:
                raise ValueError(
                    "Repository.tree(commit=...) requires a git-backed repository"
                )
            return FilesystemTreePath.from_filesystem_path(self._root)
        return GitTreePath(git, commit=commit)

    @cached_property
    def git(self) -> GitStore | None:
        """The :class:`GitStore` if this directory is git-backed, else ``None``."""

        if GitStore.is_repo(self._root):
            return GitStore.open(self._root, policy=PROPSTORE_GIT_POLICY)
        return None

    def require_git(self) -> GitStore:
        git = self.git
        if git is None:
            raise ValueError("operation requires a git-backed repository")
        return git

    @cached_property
    def _family_store(self) -> DocumentFamilyStore[object]:
        return DocumentFamilyStore[object](owner=self, backend=self.git)

    @cached_property
    def families(self) -> BoundFamilyRegistry[object, object]:
        return PROPSTORE_FAMILY_REGISTRY.bind(self, self._family_store)

    @cached_property
    def snapshot(self) -> RepositorySnapshot:
        return RepositorySnapshot(self)

    @classmethod
    def is_propstore_repo(cls, root: Path) -> bool:
        """Whether *root* is a git store carrying propstore bootstrap state."""

        if not GitStore.is_repo(root):
            return False
        git = GitStore.open(root, policy=PROPSTORE_GIT_POLICY)
        return _read_bootstrap_manifest(git) is not None

    def write_bootstrap_manifest(self, *, seed_commit: str | None = None) -> None:
        _write_bootstrap_manifest(self.require_git(), seed_commit=seed_commit)

    @contextmanager
    def mutation_guard(self) -> Iterator[None]:
        git = self.git
        if git is None:
            raise ValueError("repository mutations require a git-backed repository")
        with git.mutation_guard():
            yield

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Locate a propstore repository at or above *start* (default: cwd).

        Recognises *start* itself when it is a git-backed propstore store, then
        walks up looking for a git-backed ``knowledge/`` directory.
        """

        current = (start or Path.cwd()).resolve()
        if GitStore.is_repo(current) and cls.is_propstore_repo(current):
            return cls(current)

        for ancestor in [current, *current.parents]:
            candidate = ancestor / "knowledge"
            if not candidate.is_dir():
                continue
            if not GitStore.is_repo(candidate):
                continue
            if cls.is_propstore_repo(candidate):
                return cls(candidate)
            raise RepositoryNotFound(
                f"Git repository at {candidate} is not a propstore repository. "
                "Run 'pks init' to create one."
            )
        if GitStore.is_repo(current):
            raise RepositoryNotFound(
                f"Git repository at {current} is not a propstore repository. "
                "Run 'pks init' to create one."
            )
        raise RepositoryNotFound(
            f"No git-backed knowledge/ directory found (searched from {current}). "
            "Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create a store-only propstore repository and return it."""

        GitStore.init(root, policy=PROPSTORE_GIT_POLICY)
        repo = cls(root)
        repo.write_bootstrap_manifest()
        return repo


def _bootstrap_manifest(seed_commit: str | None) -> dict[str, object]:
    return {
        "repository_format_version": PROPSTORE_REPOSITORY_FORMAT_VERSION,
        "family_registry_contract_version": str(
            PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION
        ),
        "seed_bundle_version": "packaged-defaults",
        "seed_commit": seed_commit,
        "primary_branch": "master",
    }


def _write_bootstrap_manifest(git: GitStore, *, seed_commit: str | None) -> None:
    payload = json.dumps(
        _bootstrap_manifest(seed_commit),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    git.write_blob_ref(PROPSTORE_BOOTSTRAP_REF, payload)


def _read_bootstrap_manifest(git: GitStore) -> dict[str, object] | None:
    payload = git.read_blob_ref(PROPSTORE_BOOTSTRAP_REF)
    if payload is None:
        return None
    try:
        manifest = msgspec.json.decode(payload, type=dict[str, object])
    except msgspec.DecodeError:
        return None
    if manifest.get("repository_format_version") != PROPSTORE_REPOSITORY_FORMAT_VERSION:
        return None
    return manifest

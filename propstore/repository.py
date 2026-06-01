"""Repository — locates and provides paths within a propstore knowledge/ directory."""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TypeVar

from quire import ContractManifest, check_contract_manifest
from quire.derived_store import DerivedStoreManager
from quire.git_store import GitStore, HeadMismatchError
from quire.refs import RefName
from quire.tree_path import (
    FilesystemTreePath as FilesystemKnowledgePath,
    GitTreePath as GitKnowledgePath,
    TreePath as KnowledgePath,
)
from propstore.contracts import build_propstore_contract_manifest
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
    SchemaRef,
)
from propstore.storage import PROPSTORE_GIT_POLICY
from propstore.uri import DEFAULT_URI_AUTHORITY
from propstore.uri_authority import TaggingAuthority, parse_tagging_authority

PROPSTORE_BOOTSTRAP_REF = RefName("refs/propstore/bootstrap")
PROPSTORE_REPOSITORY_FORMAT_VERSION = "2026.04.store-only-init"
TUpdate = TypeVar("TUpdate")


class RepositoryNotFound(Exception):
    """Raised when no knowledge/ directory can be found."""


class Repository:
    """A propstore knowledge repository rooted at a ``knowledge/`` directory.

    All path resolution for concepts, claims, forms, derived stores, and
    counters goes through this object.
    """

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
        if self.git is None:
            return {}
        manifest = _read_bootstrap_manifest(self.git)
        if manifest is None:
            return {}
        raw_authority = manifest.get("uri_authority")
        config: dict[str, TaggingAuthority] = {}
        if isinstance(raw_authority, str):
            config["uri_authority"] = parse_tagging_authority(raw_authority)
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
                raise ValueError(
                    "Repository.tree(commit=...) requires a git-backed repository"
                )
            return FilesystemKnowledgePath.from_filesystem_path(self._root)
        return GitKnowledgePath(self.git, commit=commit)

    @cached_property
    def git(self):
        """Return the GitStore if this directory is git-backed, else None."""
        if GitStore.is_repo(self._root):
            return GitStore.open(self._root, policy=PROPSTORE_GIT_POLICY)
        return None

    def require_git(self) -> GitStore:
        git = self.git
        if git is None:
            raise ValueError("operation requires a git-backed repository")
        return git

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
        if not GitStore.is_repo(root):
            return False
        return (
            _read_bootstrap_manifest(GitStore.open(root, policy=PROPSTORE_GIT_POLICY))
            is not None
        )

    def write_bootstrap_manifest(
        self,
        *,
        seed_commit: str | None = None,
        uri_authority: str | None = None,
    ) -> None:
        _write_bootstrap_manifest(
            self.git,
            seed_commit=seed_commit,
            uri_authority=uri_authority,
        )

    def write_schema_ref(self) -> None:
        """Materialize the contract schema to ``refs/propstore/schema``."""
        self.families.schema.save(
            SchemaRef(),
            build_propstore_contract_manifest(),
            message="Materialize propstore contract schema",
        )

    def read_schema_ref(self) -> ContractManifest | None:
        """Load the materialized contract schema, or None if absent."""
        return self.families.schema.load(SchemaRef())

    def check_schema_compatibility(self) -> None:
        """Check the freshly-built schema against the materialized ref.

        Raises ``ContractManifestError`` when a charter change lacks a
        version bump. When the ref is absent there is nothing to compare
        against, so the check is a no-op. The schema is never auto-checked on
        open; this is an explicit dev/CI guard exposed through ``--check``.
        """
        previous = self.read_schema_ref()
        if previous is None:
            return
        check_contract_manifest(previous, build_propstore_contract_manifest())

    @contextmanager
    def mutation_guard(self):
        git = self.git
        if git is None:
            raise ValueError("repository mutations require a git-backed repository")
        with git._mutation_guard():
            yield

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root when it is a
        git-backed propstore store.
        """
        current = (start or Path.cwd()).resolve()
        if GitStore.is_repo(current) and cls.is_propstore_repo(current):
            return cls(current)

        # Walk up looking for knowledge/
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
                f"Run 'pks init' to create one."
            )
        if GitStore.is_repo(current):
            raise RepositoryNotFound(
                f"Git repository at {current} is not a propstore repository. "
                f"Run 'pks init' to create one."
            )
        raise RepositoryNotFound(
            f"No git-backed knowledge/ directory found (searched from {current}). "
            f"Run 'pks init' to create one."
        )

    @classmethod
    def init(cls, root: Path) -> Repository:
        """Create a store-only propstore repository and return it."""
        GitStore.init(root, policy=PROPSTORE_GIT_POLICY)
        repo = cls(root)
        repo.write_bootstrap_manifest()
        repo.write_schema_ref()
        return repo


def retry_live_branch_update(
    repo: Repository,
    branch: str,
    update: Callable[[str | None], TUpdate],
    *,
    attempts: int = 8,
) -> TUpdate:
    """Run an update with the live branch head, retrying stale-head failures."""

    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(attempts):
        expected_head = (
            None if repo.git is None else repo.require_git().branch_sha(branch)
        )
        try:
            return update(expected_head)
        except HeadMismatchError:
            if attempt == attempts - 1:
                raise
    raise AssertionError("unreachable")


def export_branch_tree(
    repo: Repository,
    branch: str,
    destination: Path,
) -> Path:
    git = repo.require_git()
    tip = git.branch_sha(branch)
    if tip is None:
        raise ValueError(f"Branch {branch!r} does not exist")

    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    for tree_file in git.iter_tree_files(commit=tip):
        target = _safe_tree_export_target(destination_root, tree_file.relpath)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(tree_file.content)
    return destination


def _safe_tree_export_target(destination_root: Path, relpath: str) -> Path:
    normalized_relpath = relpath.replace("\\", "/")
    posix_relpath = PurePosixPath(normalized_relpath)
    windows_relpath = PureWindowsPath(relpath)
    if (
        posix_relpath.is_absolute()
        or windows_relpath.is_absolute()
        or ".." in posix_relpath.parts
    ):
        raise ValueError(f"path escapes output_dir: {relpath}")
    target = (destination_root / Path(*posix_relpath.parts)).resolve()
    try:
        target.relative_to(destination_root)
    except ValueError as exc:
        raise ValueError(f"path escapes output_dir: {relpath}") from exc
    return target


def _bootstrap_manifest(
    seed_commit: str | None,
    uri_authority: str | None = None,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "repository_format_version": PROPSTORE_REPOSITORY_FORMAT_VERSION,
        "family_registry_contract_version": str(
            PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION
        ),
        "seed_bundle_version": "packaged-defaults",
        "seed_commit": seed_commit,
        "primary_branch": "master",
    }
    if uri_authority is not None:
        manifest["uri_authority"] = uri_authority
    return manifest


def _write_bootstrap_manifest(
    git,
    *,
    seed_commit: str | None,
    uri_authority: str | None = None,
) -> None:
    payload = json.dumps(
        _bootstrap_manifest(seed_commit, uri_authority),
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

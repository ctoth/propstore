"""Repository — locates and provides paths within a propstore knowledge/ directory."""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

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


class StaleHeadError(RuntimeError):
    """Raised when a branch-head CAS check rejects a stale mutation."""

    def __init__(
        self,
        *,
        branch: str,
        expected_head: str | None,
        actual_head: str | None,
        path: str,
    ) -> None:
        super().__init__(
            f"{path} saw stale branch {branch!r}: "
            f"expected {expected_head}, got {actual_head}"
        )
        self.branch = branch
        self.expected_head = expected_head
        self.actual_head = actual_head
        self.path = path


@dataclass(frozen=True)
class HeadBoundTransaction:
    repo: Repository
    branch: str
    expected_head: str | None = None
    path: str = "head_bound_transaction"
    _sidecar_writes: list[Callable[[], None]] = field(default_factory=list)
    _commit_sha: str | None = None
    _mutation_guard: Any | None = field(default=None, init=False, repr=False)

    @property
    def commit_sha(self) -> str | None:
        return self._commit_sha

    def __enter__(self) -> HeadBoundTransaction:
        git = self.repo.git
        if git is None:
            raise ValueError("head-bound transactions require a git-backed repository")
        guard = git._mutation_guard()
        guard.__enter__()
        object.__setattr__(self, "_mutation_guard", guard)
        object.__setattr__(self, "expected_head", self.repo.snapshot.branch_head(self.branch))
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None:
        try:
            if exc_type is not None:
                self._sidecar_writes.clear()
                return None
            if self._commit_sha is None:
                self._sidecar_writes.clear()
                return None
            for write in self._sidecar_writes:
                write()
        finally:
            self._sidecar_writes.clear()
            guard = self._mutation_guard
            object.__setattr__(self, "_mutation_guard", None)
            if guard is not None:
                guard.__exit__(exc_type, exc, tb)
        return None

    def commit_batch(
        self,
        *,
        adds: Mapping[str | Path, bytes],
        deletes: Sequence[str | Path],
        message: str,
    ) -> str:
        if self._commit_sha is not None:
            return self._commit_sha
        git = self.repo.git
        if git is None:
            raise ValueError("head-bound transactions require a git-backed repository")
        try:
            commit_sha = git.commit_batch(
                adds=adds,
                deletes=deletes,
                message=message,
                branch=self.branch,
                expected_head=self.expected_head,
            )
        except ValueError as exc:
            raise _map_stale_head_error(
                exc,
                branch=self.branch,
                expected_head=self.expected_head,
                path=self.path,
            ) from exc
        object.__setattr__(self, "_commit_sha", commit_sha)
        return commit_sha

    def assert_current(self) -> None:
        actual_head = self.repo.snapshot.branch_head(self.branch)
        if actual_head != self.expected_head:
            raise StaleHeadError(
                branch=self.branch,
                expected_head=self.expected_head,
                actual_head=actual_head,
                path=self.path,
            )

    def sidecar_write(self, write: Callable[[], None]) -> None:
        self._sidecar_writes.append(write)

    @contextmanager
    def families_transact(self, *, message: str):
        try:
            with self.repo.families.transact(
                message=message,
                branch=self.branch,
                expected_head=self.expected_head,
            ) as transaction:
                yield transaction
            object.__setattr__(self, "_commit_sha", transaction.commit_sha)
        except ValueError as exc:
            raise _map_stale_head_error(
                exc,
                branch=self.branch,
                expected_head=self.expected_head,
                path=self.path,
            ) from exc


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

    def head_bound_transaction(
        self,
        branch: str,
        *,
        path: str = "head_bound_transaction",
    ) -> HeadBoundTransaction:
        return HeadBoundTransaction(
            repo=self,
            branch=branch,
            path=path,
        )

    @classmethod
    def find(cls, start: Path | None = None) -> Repository:
        """Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory.

        Also recognises *start* itself as a repository root when it is a
        git-backed propstore store.
        """
        from propstore.storage import is_git_repo

        current = (start or Path.cwd()).resolve()
        if is_git_repo(current) and cls.is_propstore_repo(current):
            return cls(current)

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
        if is_git_repo(current):
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


def _map_stale_head_error(
    exc: ValueError,
    *,
    branch: str,
    expected_head: str | None,
    path: str,
) -> StaleHeadError:
    message = str(exc)
    if "head mismatch" not in message and "head changed" not in message:
        raise exc
    actual_head: str | None = None
    if " got " in message:
        actual_head = message.rsplit(" got ", 1)[1].strip()
    elif ", got " in message:
        actual_head = message.rsplit(", got ", 1)[1].strip()
    if actual_head == "None":
        actual_head = None
    return StaleHeadError(
        branch=branch,
        expected_head=expected_head,
        actual_head=actual_head,
        path=path,
    )


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

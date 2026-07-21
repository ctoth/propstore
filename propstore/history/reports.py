"""Owner-layer cores for repository history: log / diff / show / checkout.

Each function reads quire's git log / diff / show (or the build pipeline's
rebuild-from-commit) and returns a typed report. These are owner-layer surfaces:
the Phase-10 ``pks log`` / ``pks diff`` / ``pks show`` / ``pks checkout`` Click
adapters call them, render the reports, and map the typed errors here to exit
codes. Nothing in this module imports Click, writes to stdout/stderr, or calls
``sys.exit`` (CLI-adapter discipline, CLAUDE.md).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeGuard

from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY, PropstoreFamily
from propstore.families.merge_manifests import MergeManifest
from propstore.repository import Repository

_MERGE_MANIFEST_ROOT = PROPSTORE_FAMILY_REGISTRY.by_key(
    PropstoreFamily.MERGE_MANIFEST
).storage_root()


class BranchNotFoundError(Exception):
    """Raised when a requested history branch does not exist."""


class CommitNotFoundError(Exception):
    """Raised when a requested commit does not exist."""


class CommitHasNoConceptsError(Exception):
    """Raised when a historical checkout target has no concepts tree."""


@dataclass(frozen=True)
class FileChangeReport:
    """The added / modified / deleted paths of one commit or diff."""

    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)


@dataclass(frozen=True)
class MergeLogSummary:
    """The merge-manifest summary attached to a two-parent merge commit."""

    branch_a: str
    branch_b: str
    argument_count: int
    materialized_argument_count: int
    semantic_candidate_count: int


@dataclass(frozen=True)
class CommitShowReport:
    """One commit's author / time / message plus its file change set."""

    sha: str
    author: str
    time: str
    message: str
    changes: FileChangeReport


@dataclass(frozen=True)
class CheckoutReport:
    """The result of rebuilding the world sidecar from a historical commit."""

    commit: str
    rebuilt: bool


@dataclass(frozen=True)
class LogRecord:
    """One log entry: identity, classified operation, and optional file changes."""

    sha: str
    time: str
    branch: str
    operation: str
    message: str
    parents: tuple[str, ...]
    merge: MergeLogSummary | None = None
    added: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()


@dataclass(frozen=True)
class LogReport:
    """A branch's log: the branch name and its ordered log records."""

    branch: str
    entries: tuple[LogRecord, ...]


_LOG_OPERATION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Initialize knowledge repository$"), "init.repo"),
    (re.compile(r"^Seed default forms$"), "init.forms"),
    (re.compile(r"^Add concept:"), "concept.add"),
    (re.compile(r"^Import .+ at [0-9a-f]{12}$"), "repo.import"),
)


def classify_log_operation(message: str, parents: tuple[str, ...]) -> str:
    """Map a commit message to a stable operation label for history reports."""

    if len(parents) > 1:
        return "merge.commit"
    for pattern, label in _LOG_OPERATION_PATTERNS:
        if pattern.search(message):
            return label
    return "commit"


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    """Narrow a JSON value to ``list[object]`` (git log / show carry ``object``)."""

    return isinstance(value, list)


def _string_tuple(value: object) -> tuple[str, ...]:
    if _is_object_list(value):
        return tuple(str(item) for item in value)
    return ()


def _mapping_str(info: Mapping[str, object], key: str) -> str:
    return str(info[key])


def _file_change_report(info: Mapping[str, object]) -> FileChangeReport:
    return FileChangeReport(
        added=_string_tuple(info.get("added", ())),
        modified=_string_tuple(info.get("modified", ())),
        deleted=_string_tuple(info.get("deleted", ())),
    )


def _load_merge_summary(repo: Repository, sha: str) -> MergeLogSummary | None:
    """Summarize the merge manifest a two-parent merge commit added, if any.

    The merge manifest is a per-merge record file (Phase 9-2): it is written into
    the merge commit's tree under the ``merge_manifest`` root. We read the commit's
    added paths, load the manifest authored at this commit, and summarize the
    surviving rival arguments — never collapsing them (CLAUDE.md non-commitment).
    """

    git = repo.require_git()
    added = _string_tuple(git.show_commit(sha).get("added", ()))
    merge_manifests = repo.families.merge_manifest
    for path in added:
        if not path.startswith(f"{_MERGE_MANIFEST_ROOT}/"):
            continue
        manifest: MergeManifest | None = merge_manifests.load(
            merge_manifests.ref_from_path(path), commit=sha
        )
        if manifest is None:
            continue
        materialized = sum(
            1 for argument in manifest.arguments if argument.materialized
        )
        return MergeLogSummary(
            branch_a=manifest.branch_a,
            branch_b=manifest.branch_b,
            argument_count=len(manifest.arguments),
            materialized_argument_count=materialized,
            semantic_candidate_count=len(manifest.semantic_candidates),
        )
    return None


def build_log_record(
    repo: Repository,
    entry: Mapping[str, object],
    *,
    branch: str,
    show_files: bool,
) -> LogRecord:
    """Build one :class:`LogRecord` from a quire git-log entry."""

    message = _mapping_str(entry, "message")
    parents = _string_tuple(entry.get("parents", ()))
    operation = classify_log_operation(message, parents)
    sha = _mapping_str(entry, "sha")
    added: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()
    if show_files:
        changes = _file_change_report(repo.require_git().show_commit(sha))
        added = changes.added
        modified = changes.modified
        deleted = changes.deleted
    return LogRecord(
        sha=sha,
        time=_mapping_str(entry, "time"),
        branch=branch,
        operation=operation,
        message=message,
        parents=parents,
        merge=_load_merge_summary(repo, sha) if operation == "merge.commit" else None,
        added=added,
        modified=modified,
        deleted=deleted,
    )


def build_log_report(
    repo: Repository,
    *,
    count: int,
    branch_name: str | None,
    show_files: bool,
) -> LogReport:
    """Build a branch's :class:`LogReport` over quire's git log."""

    git = repo.git
    if git is None:
        raise ValueError("repository history requires a git-backed repository")
    branch = branch_name
    if branch is None:
        branch = git.current_branch_name() or git.primary_branch_name()
    if git.branch_sha(branch) is None:
        raise BranchNotFoundError(f"Branch not found: {branch}")
    entries = git.iter_log(max_count=count, branch=branch)
    return LogReport(
        branch=branch,
        entries=tuple(
            build_log_record(repo, entry, branch=branch, show_files=show_files)
            for entry in entries
        ),
    )


def build_diff_report(repo: Repository, commit: str | None) -> FileChangeReport:
    """Report the file changes a commit introduced (vs its first parent)."""

    return _file_change_report(repo.require_git().diff_commits(commit1=commit))


def build_commit_show_report(repo: Repository, commit: str) -> CommitShowReport:
    """Report one commit's metadata and file change set."""

    try:
        info = repo.require_git().show_commit(commit)
    except KeyError as exc:
        raise CommitNotFoundError(f"Commit not found: {commit}") from exc
    return CommitShowReport(
        sha=_mapping_str(info, "sha"),
        author=_mapping_str(info, "author"),
        time=_mapping_str(info, "time"),
        message=_mapping_str(info, "message"),
        changes=_file_change_report(info),
    )


def checkout_commit(repo: Repository, commit: str) -> CheckoutReport:
    """Rebuild the world sidecar from a historical commit's canonical snapshot.

    A checkout does not mutate storage: it rebuilds the content-addressed sidecar
    so the render layer can query the repository as of *commit*. The rebuild path
    lives in the build layer, imported lazily to keep history above it.
    """

    from propstore.derived_build import materialize_world_sidecar

    try:
        repo.require_git().show_commit(commit)
    except KeyError as exc:
        raise CommitNotFoundError(f"Commit not found: {commit}") from exc

    if not any(repo.families.concept.iter_refs(commit=commit)):
        raise CommitHasNoConceptsError("No concepts found at that commit.")

    _handle, rebuilt = materialize_world_sidecar(repo, force=True, commit=commit)
    return CheckoutReport(commit=commit, rebuilt=rebuilt)

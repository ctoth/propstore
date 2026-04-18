"""Repository history reports for CLI and structured consumers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from propstore.artifacts.refs import MergeManifestRef
from propstore.repository import Repository


class BranchNotFoundError(Exception):
    """Raised when a requested history branch does not exist."""


class CommitNotFoundError(Exception):
    """Raised when a requested commit does not exist."""


class CommitHasNoConceptsError(Exception):
    """Raised when a historical checkout target has no concepts tree."""


@dataclass(frozen=True)
class FileChangeReport:
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)


@dataclass(frozen=True)
class CommitShowReport:
    sha: str
    author: str
    time: str
    message: str
    changes: FileChangeReport


@dataclass(frozen=True)
class CheckoutReport:
    commit: str
    rebuilt: bool


@dataclass(frozen=True)
class MergeLogSummary:
    branch_a: str
    branch_b: str
    argument_count: int
    materialized_argument_count: int
    semantic_candidate_count: int

    def to_payload(self) -> dict[str, object]:
        return {
            "branch_a": self.branch_a,
            "branch_b": self.branch_b,
            "argument_count": self.argument_count,
            "materialized_argument_count": self.materialized_argument_count,
            "semantic_candidate_count": self.semantic_candidate_count,
        }


@dataclass(frozen=True)
class LogRecord:
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

    def to_payload(self, *, show_files: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "sha": self.sha,
            "time": self.time,
            "branch": self.branch,
            "operation": self.operation,
            "message": self.message,
            "parents": list(self.parents),
        }
        if self.merge is not None:
            payload["merge"] = self.merge.to_payload()
        if show_files:
            payload["added"] = list(self.added)
            payload["modified"] = list(self.modified)
            payload["deleted"] = list(self.deleted)
        return payload


@dataclass(frozen=True)
class LogReport:
    branch: str
    entries: tuple[LogRecord, ...]

    def to_payload(self, *, show_files: bool) -> dict[str, object]:
        return {
            "branch": self.branch,
            "entries": [
                entry.to_payload(show_files=show_files)
                for entry in self.entries
            ],
        }


_LOG_OPERATION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Initialize knowledge repository$"), "init.repo"),
    (re.compile(r"^Seed default forms$"), "init.forms"),
    (re.compile(r"^Add concept:"), "concept.add"),
    (re.compile(r"^Add alias "), "concept.alias_add"),
    (re.compile(r"^Rename concept:"), "concept.rename"),
    (re.compile(r"^Link "), "concept.link"),
    (re.compile(r"^Add value "), "concept.value_add"),
    (re.compile(r"^Add context:"), "context.add"),
    (re.compile(r"^Add form:"), "form.add"),
    (re.compile(r"^Remove form:"), "form.remove"),
    (re.compile(r"^Import \d+ paper claim file\(s\)$"), "papers.import"),
    (re.compile(r"^Create worldline:"), "worldline.create"),
    (re.compile(r"^Materialize worldline:"), "worldline.materialize"),
    (re.compile(r"^Delete worldline:"), "worldline.delete"),
    (re.compile(r"^Promote \d+ stance proposal file\(s\) from "), "stances.promote"),
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


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    return ()


def _file_change_report(info: dict[str, object]) -> FileChangeReport:
    return FileChangeReport(
        added=_string_tuple(info.get("added", ())),
        modified=_string_tuple(info.get("modified", ())),
        deleted=_string_tuple(info.get("deleted", ())),
    )


def _load_merge_summary(repo: Repository, sha: str) -> MergeLogSummary | None:
    manifest = repo.families.merge_manifests.load(
        MergeManifestRef(),
        commit=sha,
    )
    if manifest is None:
        return None
    merge = manifest.merge
    argument_rows = tuple(merge.arguments)
    materialized_count = sum(1 for row in argument_rows if row.materialized)
    return MergeLogSummary(
        branch_a=merge.branch_a,
        branch_b=merge.branch_b,
        argument_count=len(argument_rows),
        materialized_argument_count=materialized_count,
        semantic_candidate_count=len(merge.semantic_candidate_details),
    )


def build_log_record(
    repo: Repository,
    entry: dict[str, object],
    *,
    branch: str,
    show_files: bool,
) -> LogRecord:
    message = str(entry["message"])
    parents = _string_tuple(entry.get("parents", ()))
    operation = classify_log_operation(message, parents)
    sha = str(entry["sha"])
    added: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()
    if show_files:
        info = repo.snapshot.show_commit(sha)
        changes = _file_change_report(info)
        added = changes.added
        modified = changes.modified
        deleted = changes.deleted
    return LogRecord(
        sha=sha,
        time=str(entry["time"]),
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
    snapshot = repo.snapshot
    branch = branch_name
    if branch is None:
        branch = snapshot.current_branch_name() or snapshot.primary_branch_name()
    if snapshot.branch_head(branch) is None:
        raise BranchNotFoundError(f"Branch not found: {branch}")
    entries = snapshot.log(max_count=count, branch=branch)
    return LogReport(
        branch=branch,
        entries=tuple(
            build_log_record(
                repo,
                entry,
                branch=branch,
                show_files=show_files,
            )
            for entry in entries
        ),
    )


def build_diff_report(repo: Repository, commit: str | None) -> FileChangeReport:
    return _file_change_report(repo.snapshot.diff(commit1=commit))


def build_commit_show_report(repo: Repository, commit: str) -> CommitShowReport:
    try:
        info = repo.snapshot.show_commit(commit)
    except KeyError as exc:
        raise CommitNotFoundError(f"Commit not found: {commit}") from exc
    return CommitShowReport(
        sha=str(info["sha"]),
        author=str(info["author"]),
        time=str(info["time"]),
        message=str(info["message"]),
        changes=_file_change_report(info),
    )


def checkout_commit(repo: Repository, commit: str) -> CheckoutReport:
    from propstore.sidecar.build import build_sidecar

    try:
        repo.snapshot.show_commit(commit)
    except KeyError as exc:
        raise CommitNotFoundError(f"Commit not found: {commit}") from exc

    if not repo.families.concepts.list(commit=commit):
        raise CommitHasNoConceptsError("No concepts found at that commit.")

    rebuilt = build_sidecar(
        repo,
        repo.sidecar_path,
        force=True,
        commit_hash=commit,
    )
    return CheckoutReport(commit=commit, rebuilt=rebuilt)

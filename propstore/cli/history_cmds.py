"""Repository history CLI commands: ``pks log`` / ``diff`` / ``show`` / ``checkout``.

Thin Click adapters over the owner cores in :mod:`propstore.history`
(``build_log_report``, ``build_diff_report``, ``build_commit_show_report``,
``checkout_commit``): each parses flags, calls the owner, renders the typed
report, and maps the owner's typed errors to exit codes (CLAUDE.md "CLI adapter
discipline"). No history logic lives here.
"""

from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_yaml
from propstore.history import (
    BranchNotFoundError,
    CommitHasNoConceptsError,
    CommitNotFoundError,
    LogRecord,
    build_commit_show_report,
    build_diff_report,
    build_log_report,
    checkout_commit,
)
from propstore.reporting import json_ready


def _render_text_log(records: tuple[LogRecord, ...], *, show_files: bool) -> None:
    for record in records:
        msg_first_line = record.message.split("\n")[0]
        emit(
            f"  {record.sha[:8]}  {record.time}  "
            f"[{record.branch}]  {record.operation:<22}  {msg_first_line}"
        )
        if len(record.parents) > 1:
            parent_list = ", ".join(parent[:8] for parent in record.parents)
            emit(f"    parents: {parent_list}")
        if record.merge is not None:
            emit(
                "    merge: "
                f"{record.merge.branch_a} + {record.merge.branch_b}; "
                f"materialized={record.merge.materialized_argument_count}/"
                f"{record.merge.argument_count}; "
                f"semantic_candidates={record.merge.semantic_candidate_count}"
            )
        if not show_files:
            continue
        for path in record.added:
            emit(f"    A {path}")
        for path in record.modified:
            emit(f"    M {path}")
        for path in record.deleted:
            emit(f"    D {path}")


@click.command("log")
@click.option(
    "-n", "--count", default=20, show_default=True, help="Number of entries to show"
)
@click.option(
    "--branch",
    "branch_name",
    default=None,
    help="Branch history to inspect. Defaults to the current HEAD branch.",
)
@click.option("--show-files", is_flag=True, help="Show per-commit file changes.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "yaml"]),
    default="text",
    show_default=True,
    help="Render as human-readable text or structured YAML.",
)
@click.pass_obj
def log_cmd(
    obj: CliContext,
    count: int,
    branch_name: str | None,
    show_files: bool,
    output_format: str,
) -> None:
    """Show knowledge repository history."""
    repo = require_repo(obj)
    try:
        report = build_log_report(
            repo,
            count=count,
            branch_name=branch_name,
            show_files=show_files,
        )
    except BranchNotFoundError as exc:
        fail(exc)
    if not report.entries:
        emit("No history yet.")
        return
    if output_format == "yaml":
        emit_yaml(json_ready(report))
        return
    _render_text_log(report.entries, show_files=show_files)


@click.command("diff")
@click.argument("commit", required=False, default=None)
@click.pass_obj
def diff_cmd(obj: CliContext, commit: str | None) -> None:
    """Show files changed in COMMIT vs its parent (defaults to HEAD)."""
    repo = require_repo(obj)
    report = build_diff_report(repo, commit)
    for path in report.added:
        emit(f"  Added: {path}")
    for path in report.modified:
        emit(f"  Modified: {path}")
    for path in report.deleted:
        emit(f"  Deleted: {path}")
    if not report.has_changes:
        emit("No changes.")


@click.command("show")
@click.argument("commit")
@click.pass_obj
def show_cmd(obj: CliContext, commit: str) -> None:
    """Show details of a specific commit."""
    repo = require_repo(obj)
    try:
        report = build_commit_show_report(repo, commit)
    except CommitNotFoundError as exc:
        fail(exc, exit_code=2)
    emit(f"  Commit: {report.sha[:8]}")
    emit(f"  Author: {report.author}")
    emit(f"  Date: {report.time}")
    emit(f"  Message: {report.message}")
    emit()
    emit("  Files:")
    for path in report.changes.added:
        emit(f"    A {path}")
    for path in report.changes.modified:
        emit(f"    M {path}")
    for path in report.changes.deleted:
        emit(f"    D {path}")


@click.command("checkout")
@click.argument("commit")
@click.pass_obj
def checkout_cmd(obj: CliContext, commit: str) -> None:
    """Rebuild the sidecar from a historical commit's tree.

    Leaves git state, working tree, and source YAML untouched, but overwrites the
    derived store so subsequent world queries see the historical state until the
    next ``pks build``.
    """
    repo = require_repo(obj)
    try:
        report = checkout_commit(repo, commit)
    except (CommitNotFoundError, CommitHasNoConceptsError) as exc:
        fail(exc, exit_code=2)
    if report.rebuilt:
        emit(f"Sidecar built from commit {commit[:8]}.")
    else:
        emit(f"Sidecar already at commit {commit[:8]}.")

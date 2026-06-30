"""Source-branch lifecycle commands: init, finalize, promote, status, sync.

Each command is a thin adapter over a :mod:`propstore.source` owner function.
Owner ``ValueError``s (stale branch, "all claims blocked", missing finalize, …)
are left to propagate to the root group, which renders them as a one-line error
with a ``--traceback`` hint instead of a stack trace.
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit, emit_success, emit_table
from propstore.cli.source import source
from propstore.core.source_types import coerce_source_kind, coerce_source_origin_type
from propstore.source import (
    finalize_source_branch,
    init_source_branch,
    inspect_source_status,
    promote_source_branch,
    source_branch_name,
    sync_source_branch,
)
from propstore.source.status import SourceStatusState


@source.command("init")
@click.argument("name")
@click.option("--kind", "kind_name", required=True, help="Source kind (e.g. academic_paper).")
@click.option("--origin-type", required=True, help="How the source was located (doi/file/manual).")
@click.option("--origin-value", required=True, help="The origin locator value.")
@click.option(
    "--content-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional source content file; its ni: digest is recorded.",
)
@click.pass_obj
def source_init(
    obj: CliContext,
    name: str,
    kind_name: str,
    origin_type: str,
    origin_value: str,
    content_file: Path | None,
) -> None:
    """Create the source branch (if absent) and write its manifest."""
    repo = require_repo(obj)
    branch = init_source_branch(
        repo,
        name,
        kind=coerce_source_kind(kind_name),
        origin_type=coerce_source_origin_type(origin_type),
        origin_value=origin_value,
        content_file=content_file,
    )
    emit_success(f"Initialized {branch}")


@source.command("finalize")
@click.argument("name")
@click.pass_obj
def source_finalize(obj: CliContext, name: str) -> None:
    """Finalize a source branch (the promotability precondition + micropub compose)."""
    repo = require_repo(obj)
    sha = finalize_source_branch(repo, name)
    emit_success(f"Finalized {source_branch_name(name)} ({sha[:12]})")


@source.command("promote")
@click.argument("name")
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Require finalize status='ready' before promoting.",
)
@click.pass_obj
def source_promote(obj: CliContext, name: str, strict: bool) -> None:
    """Promote a finalized source branch into master.

    Partial by default: valid claims promote, blocked ones stay quarantined on
    the source branch and are surfaced. Promotion aborts (exit 1) only when every
    claim is blocked.
    """
    repo = require_repo(obj)
    result = promote_source_branch(repo, name, strict=strict)
    blocked_count = len(result.blocked_claims)
    if blocked_count > 0:
        emit_success(
            f"Promoted {source_branch_name(name)} to master "
            f"({blocked_count} blocked claim(s) quarantined; commit {result.commit_sha[:12]})."
        )
    else:
        emit_success(
            f"Promoted {source_branch_name(name)} to master (commit {result.commit_sha[:12]})"
        )


@source.command("status")
@click.argument("name")
@click.pass_obj
def source_status(obj: CliContext, name: str) -> None:
    """Show each source claim's would-be promotion status (ready/blocked)."""
    repo = require_repo(obj)
    report = inspect_source_status(repo, name)
    if report.state is SourceStatusState.NO_BRANCH:
        emit(f"No source branch {report.branch}.")
        return
    if report.state is SourceStatusState.NO_CLAIMS:
        emit(f"No claims on {report.branch}.")
        return

    rows: list[tuple[str, str, str]] = []
    for row in report.rows:
        if not row.diagnostics:
            rows.append((row.claim_id, row.promotion_status, "(ready)"))
            continue
        for diagnostic in row.diagnostics:
            rows.append(
                (row.claim_id, row.promotion_status, f"[{diagnostic.kind}] {diagnostic.message}")
            )
    emit_table(("CLAIM ID", "STATUS", "MESSAGE"), rows)


@source.command("sync")
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Destination directory (default ../papers/<slug>).",
)
@click.pass_obj
def source_sync(obj: CliContext, name: str, output_dir: Path | None) -> None:
    """Materialize a source branch's tree to a directory."""
    repo = require_repo(obj)
    destination = sync_source_branch(repo, name, output_dir=output_dir)
    emit_success(f"Synchronized {source_branch_name(name)} to {destination}")

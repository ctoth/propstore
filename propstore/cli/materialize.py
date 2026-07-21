"""``pks materialize`` — project committed repository state to loose files.

A thin Click adapter (CLAUDE.md "CLI adapter discipline") over
:func:`propstore.app.materialize.materialize_repository`: it builds the typed
request from flags, calls the owner core, renders the typed report, and maps the
expected :class:`MaterializeError` to a Click error. No projection logic lives
here.
"""

from __future__ import annotations

from pathlib import Path

import click

from propstore.app.materialize import (
    MaterializeError,
    MaterializeRequest,
    materialize_repository,
)
from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit, emit_key_values


@click.command("materialize")
@click.argument(
    "directory", required=False, type=click.Path(file_okay=False, path_type=Path)
)
@click.option("--commit", "commit_sha", default=None, help="Commit SHA to project.")
@click.option("--branch", default=None, help="Branch head to project.")
@click.option("--clean", is_flag=True, help="Remove stale materialized semantic files.")
@click.option("--force", is_flag=True, help="Overwrite local file content conflicts.")
@click.pass_obj
def materialize_cmd(
    obj: CliContext,
    directory: Path | None,
    commit_sha: str | None,
    branch: str | None,
    clean: bool,
    force: bool,
) -> None:
    """Project a committed propstore snapshot to loose files."""
    if commit_sha is not None and branch is not None:
        raise click.UsageError("--commit and --branch are mutually exclusive")
    request = MaterializeRequest(
        directory=directory,
        commit=commit_sha,
        branch=branch,
        clean=clean,
        force=force,
    )
    try:
        report = materialize_repository(require_repo(obj), request)
    except MaterializeError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"Materialized {report.source_commit}")
    emit_key_values(
        (
            ("written", len(report.written_paths)),
            ("deleted_stale", len(report.deleted_stale_paths)),
            ("skipped_ignored", len(report.skipped_ignored_paths)),
            ("clean", report.clean),
            ("force", report.force),
        )
    )

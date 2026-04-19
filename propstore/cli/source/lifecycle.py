"""Source branch lifecycle commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.app.sources import (
    SourceInitRequest,
    SourceNamedRequest,
    SourcePromoteRequest,
    SourceStampProvenanceRequest,
    SourceStatusState,
    SourceSyncRequest,
    finalize_source,
    init_source,
    inspect_source,
    promote_source,
    stamp_source_provenance,
    sync_source,
)
from propstore.repository import Repository
from propstore.cli.source import source


@source.command("init")
@click.argument("name")
@click.option("--kind", "kind_name", required=True)
@click.option("--origin-type", required=True)
@click.option("--origin-value", required=True)
@click.option("--content-file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_obj
def source_init(
    obj: dict,
    name: str,
    kind_name: str,
    origin_type: str,
    origin_value: str,
    content_file: Path | None,
) -> None:
    repo: Repository = obj["repo"]
    try:
        report = init_source(
            repo,
            SourceInitRequest(
                name=name,
                kind=kind_name,
                origin_type=origin_type,
                origin_value=origin_value,
                content_file=content_file,
            ),
        )
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Initialized {report.branch}")


@source.command("finalize")
@click.argument("name")
@click.pass_obj
def finalize(obj: dict, name: str) -> None:
    repo: Repository = obj["repo"]
    try:
        report = finalize_source(repo, SourceNamedRequest(name=name))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Finalized {report.branch}")


@source.command("promote")
@click.argument("name")
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help=(
        "Require finalize status='ready' before promoting; abort on any "
        "per-item finalize error. Preserves pre-render-gate-removal behavior."
    ),
)
@click.pass_obj
def promote(obj: dict, name: str, strict: bool) -> None:
    """Promote a source branch. Partial by default; valid claims promote,
    blocked ones stay on the source branch with a ``promotion_status='blocked'``
    sidecar mirror row (axis-1 finding 3.3 / ws-z-render-gates.md).

    Exit code 0 when anything promoted (including full success). Exit code 1
    when all items were blocked — the user must fix finalize errors and
    re-promote.
    """

    repo: Repository = obj["repo"]
    try:
        report = promote_source(repo, SourcePromoteRequest(name=name, strict=strict))
    except ValueError as exc:
        # When strict=True OR when all items were blocked, promote raises.
        # Preserve the ClickException path so exit code is non-zero.
        raise click.ClickException(str(exc)) from exc

    if report.blocked_count > 0:
        click.echo(
            f"Promoted {report.promoted_count} of {report.total_claims} claims to master "
            f"({report.blocked_count} blocked; see build_diagnostics)."
        )
    else:
        click.echo(f"Promoted {report.branch} to master")


@source.command("status")
@click.argument("name")
@click.pass_obj
def source_status(obj: dict, name: str) -> None:
    """Show per-claim promotion status for the named source branch.

    Lists the ``claim_core`` mirror rows written by
    ``pks source promote`` when a claim was blocked from promoting
    (``promotion_status='blocked'``), joined with the corresponding
    ``build_diagnostics`` rows for "why it blocked" context.

    Closes axis-1 finding 3.3 per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``:
    the partial-promote path leaves blocked claims visible and
    diagnosable from the primary-branch sidecar without requiring a
    round trip through ``pks source promote --strict`` or a CLI rerun.
    """
    repo: Repository = obj["repo"]
    report = inspect_source(repo, SourceNamedRequest(name=name))
    if report.state is SourceStatusState.SIDECAR_MISSING:
        click.echo("No sidecar built yet — run 'pks build' first.")
        return
    if report.state is SourceStatusState.CLAIM_CORE_MISSING:
        click.echo("No claim_core table — sidecar schema may predate phase 3.")
        return
    if report.state is SourceStatusState.NO_ROWS:
        click.echo(f"No promotion-status rows for {report.branch}.")
        return

    # Tabular text output follows the style established by `pks log`
    # (propstore/cli/__init__.py:155-187).
    header = f"{'CLAIM ID':<40}  {'STATUS':<10}  MESSAGE"
    click.echo(header)
    click.echo("-" * len(header))
    for row in report.rows:
        if not row.diagnostics:
            click.echo(f"{row.claim_id:<40}  {row.promotion_status:<10}  (no diagnostic)")
            continue
        for diag in row.diagnostics:
            click.echo(
                f"{row.claim_id:<40}  {row.promotion_status:<10}  [{diag.kind}] {diag.message}"
            )


@source.command("sync")
@click.argument("name")
@click.option("--output-dir", type=click.Path(file_okay=False, path_type=Path))
@click.pass_obj
def sync(obj: dict, name: str, output_dir: Path | None) -> None:
    repo: Repository = obj["repo"]
    try:
        report = sync_source(
            repo,
            SourceSyncRequest(name=name, output_dir=output_dir),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Synchronized {report.branch} to {report.destination}")


@source.command("stamp-provenance")
@click.argument("name")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--agent", required=True)
@click.option("--skill", "skill_name", required=True)
@click.option("--plugin-version", required=False)
def stamp_provenance(
    name: str,
    file_path: Path,
    agent: str,
    skill_name: str,
    plugin_version: str | None,
) -> None:
    """Stamp extraction provenance onto a pipeline artifact.

    DEPRECATED: Use --reader/--method flags on add-claim, add-justification,
    add-stance instead. Provenance is now stored on the source branch directly.
    """
    stamped_path = stamp_source_provenance(
        SourceStampProvenanceRequest(
            file_path=file_path,
            agent=agent,
            skill_name=skill_name,
            plugin_version=plugin_version,
        )
    )
    click.echo(f"Stamped provenance on {stamped_path}")

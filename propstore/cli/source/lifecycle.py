"""Source branch lifecycle commands."""

from __future__ import annotations

from pathlib import Path

import click

from propstore.core.source_types import (
    coerce_source_kind,
    coerce_source_origin_type,
)
from propstore.provenance import stamp_file
from propstore.repository import Repository
from propstore.source import (
    finalize_source_branch,
    init_source_branch,
    inspect_source_status,
    promote_source_branch,
    sync_source_branch,
    source_branch_name,
    SourceStatusState,
)
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
        source_kind = coerce_source_kind(kind_name)
        source_origin_type = coerce_source_origin_type(origin_type)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    branch = init_source_branch(
        repo,
        name,
        kind=source_kind,
        origin_type=source_origin_type,
        origin_value=origin_value,
        content_file=content_file,
    )
    click.echo(f"Initialized {branch}")


@source.command("finalize")
@click.argument("name")
@click.pass_obj
def finalize(obj: dict, name: str) -> None:
    repo: Repository = obj["repo"]
    try:
        finalize_source_branch(repo, name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Finalized {source_branch_name(name)}")


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

    import sys

    repo: Repository = obj["repo"]
    try:
        promote_source_branch(repo, name, strict=strict)
    except ValueError as exc:
        # When strict=True OR when all items were blocked, promote raises.
        # Preserve the ClickException path so exit code is non-zero.
        raise click.ClickException(str(exc)) from exc

    # Count promoted vs blocked via the finalize report for user-visible
    # reporting. This re-reads state but avoids plumbing a new return type
    # through ``promote_source_branch`` in this phase.
    from propstore.source.common import load_source_finalize_report
    from propstore.source.common import load_source_claims_document

    claims_doc = load_source_claims_document(repo, name)
    report = load_source_finalize_report(repo, name)
    total_claims = len(claims_doc.claims) if claims_doc is not None else 0
    blocked_count = 0
    if report is not None:
        blocked_count = (
            len(report.claim_reference_errors)
            + len(report.justification_reference_errors)
            + len(report.stance_reference_errors)
        )
        # The error lists can reference the same claim multiple times;
        # the important user-visible detail is "some were blocked", not
        # exact cardinality. Clamp to total.
        blocked_count = min(blocked_count, total_claims)
    promoted_count = max(0, total_claims - blocked_count)

    if blocked_count > 0:
        click.echo(
            f"Promoted {promoted_count} of {total_claims} claims to master "
            f"({blocked_count} blocked; see build_diagnostics)."
        )
    else:
        click.echo(f"Promoted {source_branch_name(name)} to master")


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
    report = inspect_source_status(repo, name)
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
        destination = sync_source_branch(repo, name, output_dir=output_dir)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Synchronized {source_branch_name(name)} to {destination}")


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
    stamp_file(file_path, agent=agent, skill=skill_name, plugin_version=plugin_version)
    click.echo(f"Stamped provenance on {file_path}")

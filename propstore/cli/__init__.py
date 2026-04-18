"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

from pathlib import Path
import sys

import click

from propstore.artifacts.codecs import render_yaml_value
from propstore.cli.concept import concept
from propstore.cli.context import context
from propstore.cli.claim import claim
from propstore.cli.compiler_cmds import validate, build, query, export_aliases, world
from propstore.cli.grounding_cmds import grounding
from propstore.cli.source import source
from propstore.cli.verify import verify
from propstore.cli.worldline_cmds import worldline
from propstore.cli.form import form
from propstore.cli.init import init
from propstore.cli.merge_cmds import merge
from propstore.cli.micropub import micropub
from propstore.cli.repository_import_cmd import import_repository_cmd
from propstore.repository_history import (
    BranchNotFoundError,
    CommitHasNoConceptsError,
    CommitNotFoundError,
    LogRecord,
    build_commit_show_report,
    build_diff_report,
    build_log_report,
    checkout_commit,
)
from propstore.repository import Repository


class _LazyRepository:
    def __init__(self, start: Path | None) -> None:
        self._start = start
        self._repo: Repository | None = None

    def _resolve(self) -> Repository:
        if self._repo is None:
            self._repo = Repository.find(self._start)
        return self._repo

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


@click.group()
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
@click.pass_context
def cli(ctx: click.Context, directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    start = Path(directory) if directory else None
    if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        return
    if ctx.invoked_subcommand == "init":
        # init bypasses Repository lookup — store the start dir for init to use
        ctx.obj["start"] = start
        return
    ctx.obj["repo"] = _LazyRepository(start)


cli.add_command(concept)
cli.add_command(context)
cli.add_command(claim)
cli.add_command(form)
cli.add_command(source)
cli.add_command(verify)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(init)
cli.add_command(world)
cli.add_command(worldline)
cli.add_command(grounding)
cli.add_command(merge)
cli.add_command(micropub)
cli.add_command(import_repository_cmd)


# ── log command ─────────────────────────────────────────────────────

def _render_text_log(records: tuple[LogRecord, ...], *, show_files: bool) -> None:
    for record in records:
        sha_short = record.sha[:8]
        time_str = record.time
        branch = record.branch
        operation = record.operation
        msg_first_line = record.message.split("\n")[0]
        click.echo(f"  {sha_short}  {time_str}  [{branch}]  {operation:<22}  {msg_first_line}")
        parents = record.parents
        if len(parents) > 1:
            parent_list = ", ".join(parent[:8] for parent in parents)
            click.echo(f"    parents: {parent_list}")
        if record.merge is not None:
            click.echo(
                "    merge: "
                f"{record.merge.branch_a} + {record.merge.branch_b}; "
                f"materialized={record.merge.materialized_argument_count}/{record.merge.argument_count}; "
                f"semantic_candidates={record.merge.semantic_candidate_count}"
            )
        if not show_files:
            continue
        for path in record.added:
            click.echo(f"    A {path}")
        for path in record.modified:
            click.echo(f"    M {path}")
        for path in record.deleted:
            click.echo(f"    D {path}")


@cli.command("log")
@click.option("-n", "--count", default=20, show_default=True, help="Number of entries to show")
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
@click.pass_context
def log_cmd(ctx, count, branch_name, show_files, output_format):
    """Show knowledge repository history."""
    repo = ctx.obj["repo"]
    try:
        report = build_log_report(
            repo,
            count=count,
            branch_name=branch_name,
            show_files=show_files,
        )
    except BranchNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    if not report.entries:
        click.echo("No history yet.")
        return
    if output_format == "yaml":
        click.echo(render_yaml_value(report.to_payload(show_files=show_files)))
        return
    _render_text_log(report.entries, show_files=show_files)


# ── diff command ─────────────────────────────────────────────────────

@cli.command("diff")
@click.argument("commit", required=False, default=None)
@click.pass_context
def diff_cmd(ctx, commit):
    """Show files changed in COMMIT vs its parent (defaults to HEAD)."""
    repo = ctx.obj["repo"]
    report = build_diff_report(repo, commit)
    for path in report.added:
        click.echo(f"  Added: {path}")
    for path in report.modified:
        click.echo(f"  Modified: {path}")
    for path in report.deleted:
        click.echo(f"  Deleted: {path}")
    if not report.has_changes:
        click.echo("No changes.")


# ── show command ─────────────────────────────────────────────────────

@cli.command("show")
@click.argument("commit")
@click.pass_context
def show_cmd(ctx, commit):
    """Show details of a specific commit."""
    repo = ctx.obj["repo"]
    try:
        report = build_commit_show_report(repo, commit)
    except CommitNotFoundError:
        click.echo(f"Commit not found: {commit}")
        return
    click.echo(f"  Commit: {report.sha[:8]}")
    click.echo(f"  Author: {report.author}")
    click.echo(f"  Date: {report.time}")
    click.echo(f"  Message: {report.message}")
    click.echo()
    click.echo("  Files:")
    for path in report.changes.added:
        click.echo(f"    A {path}")
    for path in report.changes.modified:
        click.echo(f"    M {path}")
    for path in report.changes.deleted:
        click.echo(f"    D {path}")


# ── checkout command ─────────────────────────────────────────────────

@cli.command("checkout")
@click.argument("commit")
@click.pass_context
def checkout_cmd(ctx, commit):
    """Rebuild the sidecar from a historical commit's tree.

    Leaves git state, working tree, and source YAML untouched, but
    overwrites the on-disk sidecar at ``<repo>/sidecar/propstore.sqlite``
    so that subsequent ``pks world`` / ``pks query`` commands see the
    historical state until the next ``pks build``.
    """
    repo = ctx.obj["repo"]

    try:
        report = checkout_commit(repo, commit)
    except CommitNotFoundError:
        click.echo(f"Commit not found: {commit}")
        return
    except CommitHasNoConceptsError:
        click.echo("No concepts found at that commit.")
        return

    if report.rebuilt:
        click.echo(f"Sidecar built from commit {commit[:8]}.")
    else:
        click.echo(f"Sidecar already at commit {commit[:8]}.")


# ── promote command ──────────────────────────────────────────────────

@cli.command()
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    from propstore.proposals import (
        plan_stance_proposal_promotion,
        promote_stance_proposals,
    )

    repo: "Repository" = ctx.obj["repo"]
    plan = plan_stance_proposal_promotion(repo, path=path)
    if not plan.has_branch:
        click.echo(f"No {plan.branch} branch found. Nothing to promote.")
        return

    if not plan.items:
        click.echo(f"No stance proposal files found on {plan.branch}.")
        return

    for item in plan.items:
        click.echo(f"  {item.source_relpath} -> {item.target_path}")

    if not yes:
        click.confirm("Promote these files?", abort=True)

    result = promote_stance_proposals(repo, plan)
    for item in plan.items:
        click.echo(f"  Promoted: {item.filename}")

    click.echo(f"\n{result.moved} file(s) promoted.")

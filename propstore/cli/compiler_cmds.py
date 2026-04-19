"""Compiler-facing CLI commands.

Exposes top-level commands for validation, sidecar builds, raw sidecar SQL,
and alias export.
"""
from __future__ import annotations

import json
import sys

import click

from propstore.app.compiler import (
    CompilerWorkflowError,
    SidecarQueryError,
    SidecarQueryRequest,
    build_repository,
    export_aliases as run_export_aliases,
    query_sidecar,
    validate_repository,
)
from propstore.cli.helpers import EXIT_VALIDATION
from propstore.repository import Repository


def _emit_workflow_messages(messages) -> None:
    for message in messages:
        label = message.level.upper()
        if message.scope:
            label = f"{label} ({message.scope})"
        click.echo(f"{label}: {message.text}", err=True)


@click.command()
@click.pass_obj
def validate(obj: dict) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    repo: Repository = obj["repo"]
    try:
        report = validate_repository(repo)
    except CompilerWorkflowError as exc:
        _emit_workflow_messages(exc.messages)
        click.echo(exc.summary, err=True)
        sys.exit(EXIT_VALIDATION)

    if report.no_concepts:
        click.echo("No concept files found.")
        return

    _emit_workflow_messages(report.messages)
    if report.ok:
        click.echo(
            f"Validation passed: {report.concept_count} concept(s), "
            f"{report.claim_file_count} claim file(s)")
    else:
        click.echo(f"Validation FAILED: {len(report.errors)} error(s)", err=True)
        sys.exit(EXIT_VALIDATION)


@click.command()
@click.option("-o", "--output", default=None, help="Output path")
@click.option("--force", is_flag=True, help="Force rebuild")
@click.pass_obj
def build(obj: dict, output: str | None, force: bool) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    repo: Repository = obj["repo"]
    try:
        report = build_repository(repo, output=output, force=force)
    except CompilerWorkflowError as exc:
        _emit_workflow_messages(exc.messages)
        click.echo(exc.summary, err=True)
        sys.exit(EXIT_VALIDATION)

    if report.no_concepts:
        click.echo("No concept files found.")
        return

    _emit_workflow_messages(report.messages)
    for conflict in report.conflicts:
        click.echo(
            f"  {conflict.warning_class}: {conflict.concept_id} "
            f"({conflict.claim_a_id} vs {conflict.claim_b_id})",
            err=True,
        )
    for group in report.phi_groups:
        click.echo(
            f"  {group.key} — {len(group.claim_ids)} branches: "
            f"{', '.join(group.claim_ids)}",
            err=True,
        )

    status = "rebuilt" if report.rebuilt else "unchanged"
    click.echo(
        f"Build {status}: {report.concept_count} concepts, "
        f"{report.claim_count} claims, {report.conflict_count} conflicts, "
        f"{report.phi_node_count} phi-nodes, {report.warning_count} warnings")


@click.command()
@click.argument("sql")
@click.pass_obj
def query(obj: dict, sql: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    repo: Repository = obj["repo"]
    try:
        result = query_sidecar(repo, SidecarQueryRequest(sql=sql))
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)
    except SidecarQueryError as exc:
        click.echo(f"SQL error: {exc}", err=True)
        sys.exit(1)

    if not result.rows:
        click.echo("(no results)")
        return
    click.echo("\t".join(result.columns))
    for row in result.rows:
        click.echo("\t".join(row))


@click.command("export-aliases")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              help="Output format")
@click.pass_obj
def export_aliases(obj: dict, fmt: str) -> None:
    """Export the alias lookup table."""
    repo: Repository = obj["repo"]
    try:
        aliases = run_export_aliases(repo)
    except FileNotFoundError:
        click.echo("ERROR: No concepts directory.", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(
            {alias: entry.to_dict() for alias, entry in aliases.items()},
            indent=2,
        ))
    else:
        for alias_name, info in sorted(aliases.items()):
            click.echo(f"{alias_name} -> {info.logical_id} ({info.name})")


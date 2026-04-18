"""pks micropub - inspect and lift micropublication bundles."""

from __future__ import annotations

import sys

import click

from quire.documents import render_yaml_value
from propstore.micropubs import (
    MicropubNotFoundError,
    find_micropub,
    inspect_micropub_lift,
    load_micropub_bundle,
)
from propstore.repository import Repository
from propstore.cli.helpers import EXIT_ERROR


@click.group()
def micropub() -> None:
    """Inspect micropublications."""


@micropub.command("bundle")
@click.argument("source")
@click.pass_obj
def bundle(obj: dict, source: str) -> None:
    """Render the canonical micropublication bundle for a source."""
    repo: Repository = obj["repo"]
    try:
        document = load_micropub_bundle(repo, source)
    except MicropubNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_ERROR)
    click.echo(render_yaml_value(document.to_payload()).rstrip())


@micropub.command("show")
@click.argument("artifact_id")
@click.pass_obj
def show(obj: dict, artifact_id: str) -> None:
    """Render one micropublication by artifact id."""
    repo: Repository = obj["repo"]
    try:
        entry = find_micropub(repo, artifact_id)
    except MicropubNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_ERROR)
    click.echo(render_yaml_value(entry.document.to_payload()).rstrip())


@micropub.command("lift")
@click.argument("artifact_id")
@click.option("--target-context", required=True)
@click.pass_obj
def lift(obj: dict, artifact_id: str, target_context: str) -> None:
    """Report whether a micropublication can lift to a target context."""
    repo: Repository = obj["repo"]
    try:
        report = inspect_micropub_lift(
            repo,
            artifact_id,
            target_context=target_context,
        )
    except MicropubNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_ERROR)
    if not report.liftable:
        click.echo(
            f"not liftable: {report.artifact_id} {report.source_context} -> {report.target_context}"
        )
        sys.exit(EXIT_ERROR)
    click.echo(
        f"liftable: {report.artifact_id} {report.source_context} -> {report.target_context}"
    )

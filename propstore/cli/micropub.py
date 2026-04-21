"""pks micropub - inspect and lift micropublication bundles."""

from __future__ import annotations

import click

from propstore.cli.output import emit, emit_yaml

from propstore.app.micropubs import (
    MicropubNotFoundError,
    find_micropub,
    inspect_micropub_lift,
    load_micropub_bundle,
)
from propstore.repository import Repository
from propstore.cli.helpers import EXIT_ERROR, exit_with_code, fail


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
        fail(exc)
    emit_yaml(document.to_payload())


@micropub.command("show")
@click.argument("artifact_id")
@click.pass_obj
def show(obj: dict, artifact_id: str) -> None:
    """Render one micropublication by artifact id."""
    repo: Repository = obj["repo"]
    try:
        entry = find_micropub(repo, artifact_id)
    except MicropubNotFoundError as exc:
        fail(exc)
    emit_yaml(entry.document.to_payload())


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
        fail(exc)
    if not report.liftable:
        emit(
            f"not liftable: {report.artifact_id} {report.source_context} -> {report.target_context}"
        )
        exit_with_code(EXIT_ERROR)
    emit(
        f"liftable: {report.artifact_id} {report.source_context} -> {report.target_context}"
    )

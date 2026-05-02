"""pks micropub - inspect and lift micropublication bundles."""

from __future__ import annotations

import click

from propstore.cli.output import emit, emit_table, emit_yaml

from propstore.app.micropubs import (
    MicropubNotFoundError,
    find_micropub,
    inspect_micropub_lift,
    list_micropubs,
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


@micropub.command("list")
@click.pass_obj
def list_cmd(obj: dict) -> None:
    """List micropublication entries across bundles."""
    repo: Repository = obj["repo"]
    items = list_micropubs(repo)
    if not items:
        emit("No micropublications.")
        return
    emit_table(
        ("BUNDLE", "ARTIFACT ID", "CONTEXT"),
        [
            (item.bundle, item.artifact_id, item.context_id)
            for item in items
        ],
    )


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
    """Report micropublication lifting decisions for a target context."""
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
            f"no lifted decision: {report.artifact_id} {report.source_context} -> {report.target_context}"
        )
        exit_with_code(EXIT_ERROR)
    emit(
        f"lifting decisions: {report.artifact_id} {report.source_context} -> {report.target_context}"
    )
    emit_table(
        ("CLAIM", "RULE", "STATUS", "MODE", "EXCEPTION"),
        [
            (
                decision.proposition_id,
                decision.rule_id,
                decision.status,
                decision.mode,
                decision.exception_id or "",
            )
            for decision in report.decisions
        ],
    )

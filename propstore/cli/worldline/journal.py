"""Worldline journal CLI commands."""
from __future__ import annotations

import click

from propstore.app.worldlines import (
    WorldlineAtStepRequest,
    WorldlineBuildJournalRequest,
    WorldlineValidationError,
    build_worldline_journal,
    worldline_at_step as run_worldline_at_step,
)
from propstore.cli.helpers import fail
from propstore.cli.output import emit_success
from propstore.cli.worldline import worldline
from propstore.repository import Repository


@worldline.command("build-journal")
@click.argument("name")
@click.pass_obj
def worldline_build_journal(obj: dict, name: str) -> None:
    """Capture a transition journal for a saved worldline revision."""
    repo: Repository = obj["repo"]
    try:
        report = build_worldline_journal(
            repo,
            WorldlineBuildJournalRequest(name=name),
        )
    except WorldlineValidationError as exc:
        fail(exc)
    emit_success(f"Built journal for worldline '{report.name}' ({report.step_count} steps)")


@worldline.command("at-step")
@click.argument("name")
@click.argument("step", type=int)
@click.option("--heavy", is_flag=True, help="Rebuild step view with heavy replay")
@click.pass_obj
def worldline_at_step(obj: dict, name: str, step: int, heavy: bool) -> None:
    """Print claim ids accepted at a journal step."""
    repo: Repository = obj["repo"]
    try:
        report = run_worldline_at_step(
            repo,
            WorldlineAtStepRequest(name=name, step=step, heavy=heavy),
        )
    except WorldlineValidationError as exc:
        fail(exc)
    for claim_id in report.claim_ids:
        click.echo(claim_id)

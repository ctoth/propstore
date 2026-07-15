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
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_success
from propstore.cli.worldline import worldline


@worldline.command("build-journal")
@click.argument("name")
@click.pass_obj
def worldline_build_journal(obj: CliContext, name: str) -> None:
    """Capture a transition journal for a saved worldline revision."""
    repo = require_repo(obj)
    try:
        report = build_worldline_journal(
            repo, WorldlineBuildJournalRequest(name=name)
        )
    except WorldlineValidationError as exc:
        fail(exc)
    emit_success(
        f"Built journal for worldline '{report.name}' ({report.step_count} steps)"
    )


@worldline.command("at-step")
@click.argument("name")
@click.argument("step", type=int)
@click.option("--heavy", is_flag=True, help="Rebuild step view with heavy replay")
@click.pass_obj
def worldline_at_step(obj: CliContext, name: str, step: int, heavy: bool) -> None:
    """Print claim ids accepted at a journal step.

    With ``--heavy`` also print the stances and conflicts that fall within the
    accepted claim set.
    """
    repo = require_repo(obj)
    try:
        report = run_worldline_at_step(
            repo, WorldlineAtStepRequest(name=name, step=step, heavy=heavy)
        )
    except WorldlineValidationError as exc:
        fail(exc)
    for claim_id in report.claim_ids:
        emit(claim_id)
    for stance in report.stances:
        stance_type = "?" if stance.stance_type is None else stance.stance_type.value
        emit(f"stance: {stance.source_claim_id} {stance_type} {stance.target_claim_id}")
    for conflict in report.conflicts:
        emit(
            f"conflict: {conflict.claim_a_id} vs {conflict.claim_b_id} "
            f"on {conflict.concept_id} ({conflict.warning_class.value})"
        )

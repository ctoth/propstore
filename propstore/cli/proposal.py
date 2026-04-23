"""pks proposal - proposal promotion commands."""

from __future__ import annotations

import click

from propstore.app.proposals import (
    ProposalPromotionRequest,
    plan_proposal_promotion,
    promote_proposals,
)
from propstore.cli.output import emit, emit_success, emit_table


@click.group()
def proposal() -> None:
    """Manage proposal branches and proposal artifacts."""


@proposal.command("promote")
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    repo = ctx.obj["repo"]
    plan = plan_proposal_promotion(repo, ProposalPromotionRequest(path=path))
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return

    if not plan.items:
        emit(f"No stance proposal files found on {plan.branch}.")
        return

    emit_table(
        ("SOURCE", "TARGET"),
        [(item.source_relpath, item.target_path) for item in plan.items],
    )

    if not yes:
        click.confirm("Promote these files?", abort=True)

    result = promote_proposals(repo, plan)
    for item in result.promoted_items:
        emit_success(f"  Promoted: {item.filename}")

    emit_success(f"\nPromoted {result.moved} of {len(plan.items)} file(s).")

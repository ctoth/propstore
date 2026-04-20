"""Top-level proposal promotion CLI commands."""

from __future__ import annotations

import click

from propstore.cli.output import emit

from propstore.app.proposals import (
    ProposalPromotionRequest,
    plan_proposal_promotion,
    promote_proposals,
)


@click.command("promote")
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote_cmd(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    repo = ctx.obj["repo"]
    plan = plan_proposal_promotion(repo, ProposalPromotionRequest(path=path))
    if not plan.has_branch:
        emit(f"No {plan.branch} branch found. Nothing to promote.")
        return

    if not plan.items:
        emit(f"No stance proposal files found on {plan.branch}.")
        return

    for item in plan.items:
        emit(f"  {item.source_relpath} -> {item.target_path}")

    if not yes:
        click.confirm("Promote these files?", abort=True)

    result = promote_proposals(repo, plan)
    for item in plan.items:
        emit(f"  Promoted: {item.filename}")

    emit(f"\n{result.moved} file(s) promoted.")

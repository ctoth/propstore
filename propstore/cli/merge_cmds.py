"""CLI commands for formal repository merge inspection and execution."""
from __future__ import annotations

import click

from propstore.app.merge import (
    MergeCommitRequest,
    MergeInspectRequest,
    commit_merge,
    inspect_merge,
)
from quire.documents import render_yaml_value


@click.group()
def merge() -> None:
    """Inspect and execute formal repository merges."""


@merge.command("inspect")
@click.argument("branch_a")
@click.argument("branch_b")
@click.option(
    "--semantics",
    type=click.Choice(["grounded", "preferred", "stable"]),
    default="grounded",
    show_default=True,
)
@click.pass_context
def merge_inspect(ctx: click.Context, branch_a: str, branch_b: str, semantics: str) -> None:
    """Inspect the formal merge framework between two branches."""
    repo = ctx.obj["repo"]
    report = inspect_merge(
        repo,
        MergeInspectRequest(
            branch_a=branch_a,
            branch_b=branch_b,
            semantics=semantics,
        ),
    )
    click.echo(render_yaml_value(report.payload))


@merge.command("commit")
@click.argument("branch_a")
@click.argument("branch_b")
@click.option("--message", default="", help="Commit message.")
@click.option("--target-branch", default=None, help="Target branch for the merge commit.")
@click.pass_context
def merge_commit_cmd(
    ctx: click.Context,
    branch_a: str,
    branch_b: str,
    message: str,
    target_branch: str | None,
) -> None:
    """Create a storage merge commit from the formal merge framework."""
    repo = ctx.obj["repo"]
    report = commit_merge(
        repo,
        MergeCommitRequest(
            branch_a=branch_a,
            branch_b=branch_b,
            message=message,
            target_branch=target_branch,
        ),
    )
    click.echo(render_yaml_value(report.payload))

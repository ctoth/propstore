"""``pks merge`` — formal repository merge inspection and execution.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): inspect and commit
call the application owner and render its report, including target admission.
No merge logic lives here.
"""

from __future__ import annotations

import click

from propstore.app.merge import (
    MergeCommitRequest, MergeInspectRequest, commit_merge, inspect_merge,
)
from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit_yaml


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
@click.option("--target-branch", default=None, help="Target branch for the proposed merge.")
@click.pass_obj
def inspect(
    obj: CliContext, branch_a: str, branch_b: str, semantics: str,
    target_branch: str | None,
) -> None:
    """Inspect the formal merge framework between two branches."""
    repo = require_repo(obj)
    report = inspect_merge(
        repo, MergeInspectRequest(branch_a, branch_b, semantics, target_branch)
    )
    emit_yaml(report.to_json())


@merge.command("commit")
@click.argument("branch_a")
@click.argument("branch_b")
@click.option("--message", default="", help="Commit message.")
@click.option(
    "--target-branch", default=None, help="Target branch for the merge commit."
)
@click.pass_obj
def commit(
    obj: CliContext,
    branch_a: str,
    branch_b: str,
    message: str,
    target_branch: str | None,
) -> None:
    """Create a storage merge commit from the formal merge framework."""
    repo = require_repo(obj)
    report = commit_merge(
        repo,
        MergeCommitRequest(
            branch_a=branch_a,
            branch_b=branch_b,
            message=message,
            target_branch=target_branch,
        ),
    )
    emit_yaml(report.to_json())

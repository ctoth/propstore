"""``pks merge`` — formal repository merge inspection and execution.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): ``merge inspect``
summarizes the formal merge framework owner-side
(:func:`~propstore.merge.summarize_merge_framework` over
:func:`~propstore.merge.build_repository_merge_framework`) and renders the dict;
``merge commit`` calls the owner facade :func:`~propstore.app.merge.commit_merge`
and renders its typed report. No merge logic lives here.
"""

from __future__ import annotations

import click

from propstore.app.merge import MergeCommitRequest, commit_merge
from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit_yaml
from propstore.merge import (
    build_repository_merge_framework,
    summarize_merge_framework,
)


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
@click.pass_obj
def inspect(obj: CliContext, branch_a: str, branch_b: str, semantics: str) -> None:
    """Inspect the formal merge framework between two branches."""
    repo = require_repo(obj)
    summary = summarize_merge_framework(
        build_repository_merge_framework(repo, branch_a, branch_b),
        semantics=semantics,
    )
    emit_yaml(summary)


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

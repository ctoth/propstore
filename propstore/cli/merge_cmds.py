"""CLI commands for formal repository merge inspection and execution."""
from __future__ import annotations

import click
import yaml


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
    from propstore.repo.merge_classifier import build_merge_framework
    from propstore.repo.merge_report import summarize_merge_framework

    repo = ctx.obj["repo"]
    if repo.git is None:
        raise click.ClickException("merge inspect requires a git-backed repository")

    merge_framework = build_merge_framework(repo.git, branch_a, branch_b)
    summary = summarize_merge_framework(merge_framework, semantics=semantics)
    click.echo(yaml.safe_dump(summary, sort_keys=False).rstrip())


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
    from propstore.repo.merge_commit import create_merge_commit

    repo = ctx.obj["repo"]
    if repo.git is None:
        raise click.ClickException("merge commit requires a git-backed repository")

    resolved_target_branch = target_branch or repo.git.primary_branch_name()
    commit_sha = create_merge_commit(
        repo.git,
        branch_a,
        branch_b,
        message=message,
        target_branch=resolved_target_branch,
    )
    payload = {
        "surface": "storage_merge_commit",
        "branch_a": branch_a,
        "branch_b": branch_b,
        "target_branch": resolved_target_branch,
        "claims_path": "claims/merged.yaml",
        "manifest_path": "merge/manifest.yaml",
        "commit_sha": commit_sha,
    }
    click.echo(yaml.safe_dump(payload, sort_keys=False).rstrip())

"""CLI commands for formal repository merge inspection and execution."""
from __future__ import annotations

import click

from propstore.artifacts.families import (
    ClaimsFileRef,
    MergeManifestRef,
)
from propstore.artifacts.codecs import render_yaml_value


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
    from propstore.merge.merge_classifier import build_merge_framework
    from propstore.merge.merge_report import summarize_merge_framework

    repo = ctx.obj["repo"]
    merge_framework = build_merge_framework(repo.snapshot, branch_a, branch_b)
    summary = summarize_merge_framework(merge_framework, semantics=semantics)
    click.echo(render_yaml_value(summary))


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
    from propstore.storage.merge_commit import create_merge_commit

    repo = ctx.obj["repo"]
    resolved_target_branch = target_branch or repo.snapshot.primary_branch_name()
    commit_sha = create_merge_commit(
        repo.snapshot,
        branch_a,
        branch_b,
        message=message,
        target_branch=resolved_target_branch,
    )
    manifest = repo.families.merge_manifests.require(
        MergeManifestRef(),
        commit=commit_sha,
    )
    payload = {
        "surface": "storage_merge_commit",
        "branch_a": branch_a,
        "branch_b": branch_b,
        "target_branch": resolved_target_branch,
        "claims_path": repo.families.claims.family.address_for(repo, ClaimsFileRef("merged")).require_path(),
        "manifest_path": repo.families.merge_manifests.family.address_for(repo, MergeManifestRef()).require_path(),
        "commit_sha": commit_sha,
        "semantic_candidate_count": len(manifest.merge.semantic_candidate_details),
    }
    click.echo(render_yaml_value(payload))

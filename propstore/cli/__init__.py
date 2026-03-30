"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.concept import concept
from propstore.cli.context import context
from propstore.cli.claim import claim
from propstore.cli.compiler_cmds import validate, build, query, export_aliases, import_papers, world
from propstore.cli.worldline_cmds import worldline
from propstore.cli.form import form
from propstore.cli.init import init
from propstore.cli.merge_cmds import merge
from propstore.cli.repo_import_cmd import import_repo_cmd
from propstore.cli.repository import Repository, RepositoryNotFound


@click.group()
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
@click.pass_context
def cli(ctx: click.Context, directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    start = Path(directory) if directory else None
    if ctx.invoked_subcommand == "init":
        # init bypasses Repository lookup — store the start dir for init to use
        ctx.obj["start"] = start
        return
    try:
        ctx.obj["repo"] = Repository.find(start)
    except RepositoryNotFound as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(concept)
cli.add_command(context)
cli.add_command(claim)
cli.add_command(form)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(import_papers)
cli.add_command(init)
cli.add_command(world)
cli.add_command(worldline)
cli.add_command(merge)
cli.add_command(import_repo_cmd)


# ── log command ─────────────────────────────────────────────────────

@cli.command("log")
@click.option("-n", "--count", default=20, help="Number of entries to show")
@click.pass_context
def log_cmd(ctx, count):
    """Show knowledge repository history."""
    repo = ctx.obj["repo"]
    if repo.git is None:
        click.echo("Not a git-tracked knowledge repository.")
        return
    entries = repo.git.log(max_count=count)
    if not entries:
        click.echo("No history yet.")
        return
    for entry in entries:
        sha_short = entry["sha"][:8]
        time_str = entry["time"]
        msg_first_line = entry["message"].split("\n")[0]
        click.echo(f"  {sha_short}  {time_str}  {msg_first_line}")


# ── diff command ─────────────────────────────────────────────────────

@cli.command("diff")
@click.argument("commit", required=False, default=None)
@click.pass_context
def diff_cmd(ctx, commit):
    """Show files changed between HEAD and COMMIT (or HEAD vs parent)."""
    repo = ctx.obj["repo"]
    if repo.git is None:
        click.echo("Not a git-tracked knowledge repository.")
        return
    result = repo.git.diff_commits(commit1=commit)
    any_changes = False
    for path in result.get("added", []):
        click.echo(f"  Added: {path}")
        any_changes = True
    for path in result.get("modified", []):
        click.echo(f"  Modified: {path}")
        any_changes = True
    for path in result.get("deleted", []):
        click.echo(f"  Deleted: {path}")
        any_changes = True
    if not any_changes:
        click.echo("No changes.")


# ── show command ─────────────────────────────────────────────────────

@cli.command("show")
@click.argument("commit")
@click.pass_context
def show_cmd(ctx, commit):
    """Show details of a specific commit."""
    repo = ctx.obj["repo"]
    if repo.git is None:
        click.echo("Not a git-tracked knowledge repository.")
        return
    try:
        info = repo.git.show_commit(commit)
    except KeyError:
        click.echo(f"Commit not found: {commit}")
        return
    click.echo(f"  Commit: {info['sha'][:8]}")
    click.echo(f"  Author: {info['author']}")
    click.echo(f"  Date: {info['time']}")
    click.echo(f"  Message: {info['message']}")
    click.echo()
    click.echo("  Files:")
    for path in info.get("added", []):
        click.echo(f"    A {path}")
    for path in info.get("modified", []):
        click.echo(f"    M {path}")
    for path in info.get("deleted", []):
        click.echo(f"    D {path}")


# ── checkout command ─────────────────────────────────────────────────

@cli.command("checkout")
@click.argument("commit")
@click.pass_context
def checkout_cmd(ctx, commit):
    """Build sidecar from a historical commit (non-destructive)."""
    from propstore.build_sidecar import build_sidecar

    repo = ctx.obj["repo"]
    if repo.git is None:
        click.echo("Not a git-tracked knowledge repository.")
        return

    # Verify commit exists
    try:
        repo.git.show_commit(commit)
    except KeyError:
        click.echo(f"Commit not found: {commit}")
        return

    tree = repo.tree(commit=commit)
    if not (tree / "concepts").exists():
        click.echo("No concepts found at that commit.")
        return

    rebuilt = build_sidecar(
        tree, repo.sidecar_path, force=True,
        commit_hash=commit,
    )

    if rebuilt:
        click.echo(f"Sidecar built from commit {commit[:8]}.")
    else:
        click.echo(f"Sidecar already at commit {commit[:8]}.")


# ── promote command ──────────────────────────────────────────────────

@cli.command()
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    from propstore.proposals import STANCE_PROPOSAL_BRANCH, stance_proposal_filename

    repo: "Repository" = ctx.obj["repo"]
    target_stances = repo.stances_dir
    git = repo.git
    if git is None:
        click.echo("Not a git-tracked knowledge repository.", err=True)
        raise SystemExit(1)

    proposal_tip = git.branch_sha(STANCE_PROPOSAL_BRANCH)
    if proposal_tip is None:
        click.echo(f"No {STANCE_PROPOSAL_BRANCH} branch found. Nothing to promote.")
        return

    available_names = git.list_dir("stances", commit=proposal_tip)
    if path is not None:
        requested_name = Path(path).name
        if not requested_name.endswith(".yaml"):
            requested_name = stance_proposal_filename(requested_name)
        sources = [requested_name]
    else:
        sources = sorted(name for name in available_names if name.endswith(".yaml"))

    if not sources:
        click.echo(f"No stance proposal files found on {STANCE_PROPOSAL_BRANCH}.")
        return

    # Show what will be moved
    existing_names = set(available_names)
    selected_names = [name for name in sources if name in existing_names]
    if not selected_names:
        click.echo("No matching proposal files found to promote.")
        return
    for name in selected_names:
        click.echo(f"  {STANCE_PROPOSAL_BRANCH}:stances/{name} -> {target_stances / name}")

    if not yes:
        click.confirm("Promote these files?", abort=True)

    moved = 0
    adds = {}
    for name in selected_names:
        rel = f"stances/{name}"
        adds[rel] = git.read_file(rel, commit=proposal_tip)
    moved = len(adds)
    if moved > 0:
        for name in selected_names:
            click.echo(f"  Promoted: {name}")
        git.commit_batch(
            adds=adds,
            deletes=[],
            message=f"Promote {moved} stance proposal file(s) from {STANCE_PROPOSAL_BRANCH}",
        )
        git.sync_worktree()

    click.echo(f"\n{moved} file(s) promoted.")

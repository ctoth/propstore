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


# ── promote command ──────────────────────────────────────────────────

@cli.command()
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Move proposal artifacts from proposals/ into source-of-truth storage.

    Moves stance files from knowledge/proposals/stances/ to knowledge/stances/.
    If PATH is given, promotes only that file; otherwise promotes all files
    in knowledge/proposals/stances/.
    """
    repo: "Repository" = ctx.obj["repo"]
    proposals_stances = repo.root / "proposals" / "stances"
    target_stances = repo.stances_dir

    if path is not None:
        sources = [Path(path)]
    else:
        if not proposals_stances.exists():
            click.echo("No proposals/stances/ directory found. Nothing to promote.")
            return
        sources = sorted(proposals_stances.glob("*.yaml"))

    if not sources:
        click.echo("No proposal files found to promote.")
        return

    # Show what will be moved
    for src in sources:
        dest = target_stances / src.name
        click.echo(f"  {src} -> {dest}")

    if not yes:
        click.confirm("Promote these files?", abort=True)

    target_stances.mkdir(parents=True, exist_ok=True)
    moved = 0
    for src in sources:
        if not src.exists():
            click.echo(f"  SKIP (not found): {src}", err=True)
            continue
        dest = target_stances / src.name
        src.rename(dest)
        click.echo(f"  Promoted: {src.name}")
        moved += 1

    git = repo.git
    if git and moved > 0:
        adds = {}
        deletes = []
        for src in sources:
            dest = target_stances / src.name
            if dest.exists():
                rel = dest.relative_to(repo.root).as_posix()
                adds[rel] = dest.read_bytes()
            if not src.exists() and src.is_relative_to(repo.root):
                deletes.append(src.relative_to(repo.root).as_posix())
        git.commit_batch(adds=adds, deletes=deletes, message=f"Promote {moved} stance file(s)")
        git.sync_worktree()

    click.echo(f"\n{moved} file(s) promoted.")

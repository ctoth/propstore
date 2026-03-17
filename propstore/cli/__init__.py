"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

from pathlib import Path

import click

from propstore.cli.concept import concept
from propstore.cli.claim import claim
from propstore.cli.compiler_cmds import validate, build, query, export_aliases, import_papers, world
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
cli.add_command(claim)
cli.add_command(form)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(import_papers)
cli.add_command(init)
cli.add_command(world)

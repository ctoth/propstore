"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

from pathlib import Path
import sys

import click

from propstore.cli.concept import concept
from propstore.cli.context import context
from propstore.cli.claim import claim
from propstore.cli.compiler_cmds import validate, build, query, export_aliases
from propstore.cli.grounding_cmds import grounding
from propstore.cli.history_cmds import checkout_cmd, diff_cmd, log_cmd, show_cmd
from propstore.cli.proposal_cmds import promote_cmd
from propstore.cli.source import source
from propstore.cli.verify import verify
from propstore.cli.world_cmds import world
from propstore.cli.worldline_cmds import worldline
from propstore.cli.form import form
from propstore.cli.init import init
from propstore.cli.merge_cmds import merge
from propstore.cli.micropub import micropub
from propstore.cli.repository_import_cmd import import_repository_cmd
from propstore.repository import Repository


class _LazyRepository:
    def __init__(self, start: Path | None) -> None:
        self._start = start
        self._repo: Repository | None = None

    def _resolve(self) -> Repository:
        if self._repo is None:
            self._repo = Repository.find(self._start)
        return self._repo

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


@click.group()
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
@click.pass_context
def cli(ctx: click.Context, directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    start = Path(directory) if directory else None
    if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        return
    if ctx.invoked_subcommand == "init":
        # init bypasses Repository lookup — store the start dir for init to use
        ctx.obj["start"] = start
        return
    ctx.obj["repo"] = _LazyRepository(start)


cli.add_command(concept)
cli.add_command(context)
cli.add_command(claim)
cli.add_command(form)
cli.add_command(source)
cli.add_command(verify)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(init)
cli.add_command(world)
cli.add_command(worldline)
cli.add_command(grounding)
cli.add_command(merge)
cli.add_command(micropub)
cli.add_command(import_repository_cmd)
cli.add_command(log_cmd)
cli.add_command(diff_cmd)
cli.add_command(show_cmd)
cli.add_command(checkout_cmd)
cli.add_command(promote_cmd)

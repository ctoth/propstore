"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

import os

import click

from compiler.cli.concept import concept
from compiler.cli.claim import claim
from compiler.cli.compiler_cmds import validate, build, query, export_aliases, import_papers
from compiler.cli.init import init


@click.group()
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
def cli(directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    if directory is not None:
        os.chdir(directory)


cli.add_command(concept)
cli.add_command(claim)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(import_papers)
cli.add_command(init)

"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

import click

from compiler.cli.concept import concept
from compiler.cli.claim import claim
from compiler.cli.compiler_cmds import validate, build, query, export_aliases


@click.group()
def cli() -> None:
    """Propositional Knowledge Store CLI."""


cli.add_command(concept)
cli.add_command(claim)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)

"""Worldline mutation CLI commands."""
from __future__ import annotations

import sys

import click

from propstore.artifacts.refs import WorldlineRef
from propstore.cli.worldline import worldline
from propstore.repository import Repository


@worldline.command("delete")
@click.argument("name")
@click.pass_obj
def worldline_delete(obj: dict, name: str) -> None:
    """Delete a worldline."""
    repo: Repository = obj["repo"]
    if repo.families.worldlines.load(WorldlineRef(name)) is None:
        click.echo(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)
    repo.families.worldlines.delete(
        WorldlineRef(name),
        message=f"Delete worldline: {name}",
    )
    repo.snapshot.sync_worktree()
    click.echo(f"Deleted worldline '{name}'")


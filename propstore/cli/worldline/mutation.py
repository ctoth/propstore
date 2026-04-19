"""Worldline mutation CLI commands."""
from __future__ import annotations

import sys

import click

from propstore.app.worldlines import WorldlineNotFoundError, delete_worldline as run_delete_worldline
from propstore.cli.worldline import worldline
from propstore.repository import Repository


@worldline.command("delete")
@click.argument("name")
@click.pass_obj
def worldline_delete(obj: dict, name: str) -> None:
    """Delete a worldline."""
    repo: Repository = obj["repo"]
    try:
        run_delete_worldline(repo, name)
    except WorldlineNotFoundError:
        click.echo(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)
    click.echo(f"Deleted worldline '{name}'")


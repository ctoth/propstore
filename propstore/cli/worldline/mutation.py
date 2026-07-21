"""Worldline mutation CLI commands."""

from __future__ import annotations

import click

from propstore.app.worldlines import (
    WorldlineNotFoundError,
    delete_worldline as run_delete_worldline,
)
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit_success
from propstore.cli.worldline import worldline


@worldline.command("delete")
@click.argument("name")
@click.pass_obj
def worldline_delete(obj: CliContext, name: str) -> None:
    """Delete a worldline."""
    repo = require_repo(obj)
    try:
        run_delete_worldline(repo, name)
    except WorldlineNotFoundError:
        fail(f"Worldline '{name}' not found")
    emit_success(f"Deleted worldline '{name}'")

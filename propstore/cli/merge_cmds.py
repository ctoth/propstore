"""CLI commands for formal repository merge inspection and execution."""

from __future__ import annotations

import click

from propstore.cli.output import emit_yaml

from propstore.app.merge import (
    MergeCommitRequest,
    MergeInspectRequest,
    commit_merge,
    inspect_merge,
)


@click.group()
def merge() -> None:
    """Inspect and execute formal repository merges."""

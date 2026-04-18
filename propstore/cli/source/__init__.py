"""pks source - source lifecycle commands."""

from __future__ import annotations

import click

from propstore.repository import Repository
from propstore.source import (
    finalize_source_branch,
    source_branch_name,
)


@click.group()
def source() -> None:
    """Manage source branches and source-local artifacts."""


def _auto_finalize_source_branch(repo: Repository, name: str) -> None:
    try:
        finalize_source_branch(repo, name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Auto-finalized {source_branch_name(name)}")


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.source import authoring as _authoring
from propstore.cli.source import batch as _batch
from propstore.cli.source import lifecycle as _lifecycle
from propstore.cli.source import proposal as _proposal

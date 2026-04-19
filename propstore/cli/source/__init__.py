"""pks source - source lifecycle commands."""

from __future__ import annotations

import click


@click.group()
def source() -> None:
    """Manage source branches and source-local artifacts."""


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.source import authoring as _authoring
from propstore.cli.source import batch as _batch
from propstore.cli.source import lifecycle as _lifecycle
from propstore.cli.source import proposal as _proposal

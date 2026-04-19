"""pks concept command group."""

from __future__ import annotations

import click


@click.group()
def concept() -> None:
    """Manage concepts in the registry."""


# Import split command modules after the group is defined.
from propstore.cli.concept import alignment as _alignment
from propstore.cli.concept import display as _display
from propstore.cli.concept import embedding as _embedding
from propstore.cli.concept import mutation as _mutation

"""pks rule - DeLP rule authoring commands."""

from __future__ import annotations

import click


@click.group()
def rule() -> None:
    """Author DeLP strict, defeasible, and defeater rules."""


# Import split command modules after the group is defined.
from propstore.cli.rule import display as _display
from propstore.cli.rule import mutation as _mutation

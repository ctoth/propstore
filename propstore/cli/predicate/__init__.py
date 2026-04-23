"""pks predicate - predicate declaration commands."""

from __future__ import annotations

import click


@click.group()
def predicate() -> None:
    """Declare DeLP/Datalog predicates in the registry."""


# Import split command modules after the group is defined.
from propstore.cli.predicate import display as _display
from propstore.cli.predicate import mutation as _mutation

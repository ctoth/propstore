"""pks world - presentation adapters for compiled knowledge-base workflows."""
from __future__ import annotations

from collections.abc import Sequence

import click


@click.group()
@click.pass_obj
def world(obj: dict) -> None:
    """Query the compiled knowledge base."""
    pass


def _format_assumption_ids(assumption_ids: Sequence[str]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(str(assumption_id) for assumption_id in assumption_ids) + "]"


def parse_world_binding_args(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse raw CLI binding tokens into bindings and an optional target."""

    parsed: dict[str, str] = {}
    remaining: list[str] = []
    for arg in args:
        if "=" not in arg:
            remaining.append(arg)
            continue
        key, _, value = arg.partition("=")
        if not key:
            raise click.ClickException("world bindings require a non-empty key")
        parsed[key] = value
    return parsed, remaining[-1] if remaining else None


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.world import analysis as _analysis
from propstore.cli.world import atms as _atms
from propstore.cli.world import query as _query
from propstore.cli.world import reasoning as _reasoning
from propstore.cli.world import revision as _revision

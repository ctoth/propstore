"""pks world - query and reason over the compiled knowledge base."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

import click


if TYPE_CHECKING:
    from propstore.world import BoundWorld, QueryableAssumption, RenderPolicy, WorldModel


def _bind_world(
    wm: WorldModel,
    bindings: Mapping[str, str],
    *,
    context_id: str | None = None,
    policy: RenderPolicy | None = None,
) -> BoundWorld:
    from propstore.world import Environment
    from propstore.core.id_types import to_context_id

    environment = Environment(
        bindings=dict(bindings),
        context_id=(None if context_id is None else to_context_id(context_id)),
    )
    return wm.bind(environment=environment, policy=policy)


def _lifecycle_policy(
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    *,
    base: "RenderPolicy | None" = None,
) -> "RenderPolicy":
    """Construct (or clone) a ``RenderPolicy`` carrying the Phase 4
    lifecycle visibility flags.

    Closes axis-1 findings 3.1 / 3.2 / 3.3 per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``.
    When ``base`` is provided, the existing policy's non-visibility
    fields survive; only the three new flags are overwritten — this
    lets commands like ``pks world resolve`` (which already construct a
    feature-rich RenderPolicy) layer the new flags on without losing
    any prior configuration.
    """
    from dataclasses import replace

    from propstore.world import RenderPolicy as _RenderPolicy

    if base is None:
        return _RenderPolicy(
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )
    return replace(
        base,
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )

# ── World command group ──────────────────────────────────────────────


@click.group()
@click.pass_obj
def world(obj: dict) -> None:
    """Query the compiled knowledge base."""
    pass


def _resolve_world_target(wm, target: str) -> str:
    """Resolve a world command target by alias, concept ID, or canonical name."""
    return wm.resolve_concept(target) or target


def _parse_bindings(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse CLI args into (bindings, concept_id).

    Arguments with '=' are bindings, the last argument without '=' is concept_id.
    """
    from propstore.cli.helpers import parse_kv_pairs

    parsed_objects, remaining = parse_kv_pairs(args)
    parsed: dict[str, str] = {}
    for key, value in parsed_objects.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise click.ClickException("world bindings must be plain string key=value pairs")
        parsed[key] = value
    concept_id = remaining[-1] if remaining else None
    return parsed, concept_id


def _format_assumption_ids(assumption_ids: Sequence[str]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(str(assumption_id) for assumption_id in assumption_ids) + "]"


# Import split command modules after the group and shared helpers are defined.
from propstore.cli.world import analysis as _analysis
from propstore.cli.world import atms as _atms
from propstore.cli.world import query as _query
from propstore.cli.world import reasoning as _reasoning
from propstore.cli.world import revision as _revision

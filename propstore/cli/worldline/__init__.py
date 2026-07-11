"""``pks worldline`` — presentation adapters over the worldline owner tier.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): each command parses its
flags into a typed :mod:`propstore.app.worldlines` request, calls the owner-layer
function, and renders the typed report — mapping the ``WorldlineAppError``
hierarchy to exit codes. No worldline materialization / journal / revision
semantics live here; the owner module owns them.

This package ``__init__`` owns the ``worldline`` Click group and the shared
CLI-only helpers: the reasoning/revision option blocks and the ``key=value`` /
``--revision-atom`` parsing at the CLI boundary. The sibling command modules are
imported at the bottom, after the group and helpers exist, so each can attach its
commands via ``@worldline.command``.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, TypeGuard

import click
from click.decorators import FC

from propstore.app.worldlines import (
    argumentation_semantics_values,
    reasoning_backend_values,
)
from propstore.reporting import JsonValue
from propstore.support_revision.belief_set_adapter import (
    LEXICOGRAPHIC_OPERATOR,
    RESTRAINED_OPERATOR,
)

JsonObject = dict[str, JsonValue]


@click.group()
def worldline() -> None:
    """Materialized query artifacts — traced paths through the knowledge space."""


# ── CLI-boundary value coercion ────────────────────────────────────────────────


def _is_json_object(value: object) -> TypeGuard[Mapping[str, Any]]:
    """Narrow a decoded-JSON value to a string-keyed object at the CLI boundary.

    ``json.loads`` is an ``Any`` source; this is the standard JSON boundary guard
    (mirroring :func:`propstore.cli.world.is_json_object`) so the adapter can
    validate a ``--revision-atom`` payload without leaking unknown types.
    """

    return isinstance(value, dict)


def _is_json_array(value: object) -> TypeGuard[list[Any]]:
    """Narrow a decoded-JSON value to an array at the CLI boundary (see above)."""

    return isinstance(value, list)


def _is_cli_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if _is_json_object(value):
        return all(_is_cli_json_value(item) for item in value.values())
    if _is_json_array(value):
        return all(_is_cli_json_value(item) for item in value)
    return False


def coerce_worldline_cli_value(value: object) -> JsonValue:
    if _is_cli_json_value(value):
        return value
    return str(value)


def parse_kv_args(args: tuple[str, ...]) -> dict[str, str | int | float | bool]:
    """Parse ``key=value`` arguments into a JSON-ready dict with scalar coercion."""
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args, coerce=True)
    if remaining:
        bad = ", ".join(remaining)
        raise click.ClickException(f"expected key=value argument: {bad}")
    bindings: dict[str, str | int | float | bool] = {}
    for key, value in parsed.items():
        if value is None or not isinstance(value, str | int | float | bool):
            raise click.ClickException(f"binding {key!r} must be a scalar")
        bindings[key] = value
    return bindings


def parse_worldline_revision_atom(raw: str | None) -> JsonObject | None:
    if raw is None:
        return None
    try:
        loaded: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --revision-atom JSON: {exc}") from exc
    if not _is_json_object(loaded):
        raise click.ClickException("--revision-atom must decode to a JSON object")
    return {key: coerce_worldline_cli_value(value) for key, value in loaded.items()}


# ── shared option blocks ────────────────────────────────────────────────────────


def apply_reasoning_options(func: FC) -> FC:
    """Attach the reasoning-backend / semantics / PrAF option block."""

    func = click.option(
        "--praf-seed",
        "praf_seed",
        default=None,
        type=int,
        help="PrAF MC RNG seed (default: random)",
    )(func)
    func = click.option(
        "--praf-confidence",
        "praf_confidence",
        default=0.95,
        type=float,
        help="PrAF MC confidence level (default: 0.95)",
    )(func)
    func = click.option(
        "--praf-epsilon",
        "praf_epsilon",
        default=0.01,
        type=float,
        help="PrAF MC error tolerance (default: 0.01)",
    )(func)
    func = click.option(
        "--praf-strategy",
        "praf_strategy",
        default="auto",
        type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
        help="PrAF computation strategy (default: auto)",
    )(func)
    func = click.option(
        "--pessimism-index",
        "pessimism_index",
        default=0.5,
        type=float,
        help="Hurwicz pessimism index (default: 0.5)",
    )(func)
    func = click.option(
        "--decision-criterion",
        "decision_criterion",
        default="pignistic",
        type=click.Choice(
            [
                "pignistic",
                "projected_probability",
                "lower_bound",
                "upper_bound",
                "hurwicz",
            ]
        ),
        help="Decision criterion for opinion interpretation (default: pignistic)",
    )(func)
    func = click.option(
        "--link-principle",
        "link_principle",
        default="last",
        type=click.Choice(["last", "weakest"]),
        help="ASPIC+ link principle (default: last)",
    )(func)
    func = click.option(
        "--set-comparison",
        "set_comparison",
        default="elitist",
        type=click.Choice(["elitist", "democratic"]),
        help="Set comparison for preference ordering (default: elitist)",
    )(func)
    func = click.option(
        "--semantics",
        default="grounded",
        type=click.Choice(argumentation_semantics_values()),
        help="Argumentation semantics (default: grounded)",
    )(func)
    func = click.option(
        "--reasoning-backend",
        "reasoning_backend",
        default="claim_graph",
        type=click.Choice(reasoning_backend_values()),
        help="Argumentation backend (default: claim_graph)",
    )(func)
    return func


def apply_revision_options(func: FC) -> FC:
    """Attach the optional revision-query option block."""

    func = click.option(
        "--revision-operator",
        "revision_operator",
        default=None,
        type=click.Choice([RESTRAINED_OPERATOR, LEXICOGRAPHIC_OPERATOR]),
        help="Iterated revision operator family",
    )(func)
    func = click.option(
        "--revision-conflict",
        "revision_conflicts",
        multiple=True,
        help="Revision conflict mapping as atom_id=target[,target...]",
    )(func)
    func = click.option(
        "--revision-target",
        "revision_target",
        default=None,
        help="Revision target for contract",
    )(func)
    func = click.option(
        "--revision-atom",
        "revision_atom",
        default=None,
        help="Revision atom as JSON mapping",
    )(func)
    func = click.option(
        "--revision-operation",
        "revision_operation",
        default=None,
        type=click.Choice(["expand", "contract", "revise", "iterated_revise"]),
        help="Optional revision operation to record/run with this worldline",
    )(func)
    return func


# Import the command modules last so they can attach their commands to the
# ``worldline`` group; re-exported via ``__all__`` so the side-effect imports read
# as the package's public command surface rather than unused imports.
from propstore.cli.worldline import display, journal, materialize, mutation  # noqa: E402

__all__ = [
    "JsonObject",
    "apply_reasoning_options",
    "apply_revision_options",
    "coerce_worldline_cli_value",
    "display",
    "journal",
    "materialize",
    "mutation",
    "parse_kv_args",
    "parse_worldline_revision_atom",
    "worldline",
]

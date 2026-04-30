"""pks worldline — CLI commands for materialized query artifacts."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TypeGuard

import click

from propstore.app.worldlines import (
    JsonObject,
    JsonValue,
    WorldlineValidationError,
    argumentation_semantics_values,
    reasoning_backend_values,
)


def _is_cli_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _is_cli_json_value(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return all(_is_cli_json_value(item) for item in value)
    return False


def coerce_worldline_cli_value(value: object) -> JsonValue:
    if _is_cli_json_value(value):
        return value
    return str(value)


def _parse_kv_args(args: tuple[str, ...]) -> JsonObject:
    """Parse key=value arguments into a dict with type coercion."""
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args, coerce=True)
    if remaining:
        bad = ", ".join(remaining)
        raise click.ClickException(f"expected key=value argument: {bad}")
    return {
        key: coerce_worldline_cli_value(value)
        for key, value in parsed.items()
    }


def parse_worldline_revision_atom(raw: str | None) -> JsonObject | None:
    if raw is None:
        return None
    try:
        loaded: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --revision-atom JSON: {exc}") from exc
    if not isinstance(loaded, Mapping):
        raise click.ClickException("--revision-atom must decode to a JSON object")
    result: dict[str, JsonValue] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise click.ClickException("--revision-atom keys must be strings")
        try:
            result[key] = coerce_worldline_cli_value(value)
        except WorldlineValidationError as exc:
            raise click.ClickException(str(exc)) from exc
    return result


@click.group()
@click.pass_obj
def worldline(obj: dict) -> None:
    """Materialized query artifacts — traced paths through the knowledge space."""


# Shared click options for reasoning backend configuration.
_REASONING_OPTIONS = [
    click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
                 type=click.Choice(reasoning_backend_values()),
                 help="Argumentation backend (default: claim_graph)"),
    click.option("--semantics", default="grounded",
                 type=click.Choice(argumentation_semantics_values()),
                 help="Argumentation semantics (default: grounded)"),
    click.option("--set-comparison", "set_comparison", default="elitist",
                 type=click.Choice(["elitist", "democratic"]),
                 help="Set comparison for preference ordering (default: elitist)"),
    click.option("--link-principle", "link_principle", default="last",
                 type=click.Choice(["last", "weakest"]),
                 help="ASPIC+ link principle (default: last)"),
    click.option("--decision-criterion", "decision_criterion", default="pignistic",
                 type=click.Choice([
                     "pignistic",
                     "projected_probability",
                     "lower_bound",
                     "upper_bound",
                     "hurwicz",
                 ]),
                 help="Decision criterion for opinion interpretation (default: pignistic)"),
    click.option("--pessimism-index", "pessimism_index", default=0.5,
                 type=float, help="Hurwicz pessimism index (default: 0.5)"),
    click.option("--praf-strategy", "praf_strategy", default="auto",
                 type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
                 help="PrAF computation strategy (default: auto)"),
    click.option("--praf-epsilon", "praf_epsilon", default=0.01,
                 type=float, help="PrAF MC error tolerance (default: 0.01)"),
    click.option("--praf-confidence", "praf_confidence", default=0.95,
                 type=float, help="PrAF MC confidence level (default: 0.95)"),
    click.option("--praf-seed", "praf_seed", default=None,
                 type=int, help="PrAF MC RNG seed (default: random)"),
]


def _apply_reasoning_options(func):
    """Apply all reasoning backend click options to a command."""
    for option in reversed(_REASONING_OPTIONS):
        func = option(func)
    return func


_REVISION_OPTIONS = [
    click.option("--revision-operation", "revision_operation", default=None,
                 type=click.Choice(["expand", "contract", "revise", "iterated_revise"]),
                 help="Optional revision operation to record/run with this worldline"),
    click.option("--revision-atom", "revision_atom", default=None,
                 help="Revision atom as JSON mapping"),
    click.option("--revision-target", "revision_target", default=None,
                 help="Revision target for contract"),
    click.option("--revision-conflict", "revision_conflicts", multiple=True,
                 help="Revision conflict mapping as atom_id=target[,target...]"),
    click.option("--revision-operator", "revision_operator", default=None,
                 type=click.Choice(["restrained", "lexicographic"]),
                 help="Iterated revision operator family"),
]


def _apply_revision_options(func):
    for option in reversed(_REVISION_OPTIONS):
        func = option(func)
    return func


# Import command modules after the group and shared decorators are defined.
from propstore.cli.worldline import display as _display
from propstore.cli.worldline import materialize as _materialize
from propstore.cli.worldline import mutation as _mutation

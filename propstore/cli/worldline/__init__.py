"""pks worldline — CLI commands for materialized query artifacts."""
from __future__ import annotations

import click

from propstore.cli.output import emit_warning

from propstore.app.worldlines import (
    JsonObject,
    argumentation_semantics_values,
    coerce_worldline_cli_value,
    reasoning_backend_values,
)


def _parse_kv_args(args: tuple[str, ...]) -> JsonObject:
    """Parse key=value arguments into a dict with type coercion."""
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args, coerce=True)
    for r in remaining:
        emit_warning(f"WARNING: ignoring argument without '=': {r}")
    return {
        key: coerce_worldline_cli_value(value)
        for key, value in parsed.items()
    }


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
                 type=click.Choice(["pignistic", "lower_bound", "upper_bound", "hurwicz"]),
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

"""pks worldline — CLI commands for materialized query artifacts."""
from __future__ import annotations

import json
from typing import Any

import click

from propstore.artifacts.families import WorldlineRef
from propstore.repository import Repository
from propstore.world.types import (
    ReasoningBackend,
    cli_argumentation_semantics_values,
    normalize_argumentation_semantics,
    validate_backend_semantics,
)


def _parse_kv_args(args: tuple[str, ...]) -> dict[str, Any]:
    """Parse key=value arguments into a dict with type coercion."""
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args, coerce=True)
    for r in remaining:
        click.echo(f"WARNING: ignoring argument without '=': {r}", err=True)
    return parsed


@click.group()
@click.pass_obj
def worldline(obj: dict) -> None:
    """Materialized query artifacts — traced paths through the knowledge space."""


def _load_worldline_definition(repo: Repository, name: str):
    from propstore.worldline import WorldlineDefinition

    document = repo.families.worldlines.load(WorldlineRef(name))
    if document is None:
        raise FileNotFoundError(name)
    return WorldlineDefinition.from_document(document)


def _build_policy_dict(
    strategy: str | None,
    reasoning_backend: str,
    semantics: str,
    set_comparison: str,
    link_principle: str,
    decision_criterion: str,
    pessimism_index: float,
    praf_strategy: str,
    praf_epsilon: float,
    praf_confidence: float,
    praf_seed: int | None,
) -> dict[str, Any] | None:
    """Build a policy dict from CLI flags, omitting defaults.

    Returns None if no policy fields differ from RenderPolicy defaults.
    """
    try:
        normalized_backend, normalized_semantics = validate_backend_semantics(
            reasoning_backend,
            semantics,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    policy: dict[str, Any] = {}
    if strategy:
        policy["strategy"] = strategy
    if normalized_backend != ReasoningBackend.CLAIM_GRAPH:
        policy["reasoning_backend"] = normalized_backend.value
    if normalized_semantics != normalize_argumentation_semantics("grounded"):
        policy["semantics"] = normalized_semantics.value
    if set_comparison != "elitist":
        policy["comparison"] = set_comparison
    if link_principle != "last":
        policy["link"] = link_principle
    if decision_criterion != "pignistic":
        policy["decision_criterion"] = decision_criterion
    if pessimism_index != 0.5:
        policy["pessimism_index"] = pessimism_index
    if praf_strategy != "auto":
        policy["praf_strategy"] = praf_strategy
    if praf_epsilon != 0.01:
        policy["praf_mc_epsilon"] = praf_epsilon
    if praf_confidence != 0.95:
        policy["praf_mc_confidence"] = praf_confidence
    if praf_seed is not None:
        policy["praf_mc_seed"] = praf_seed
    return policy or None


# Shared click options for reasoning backend configuration.
_REASONING_OPTIONS = [
    click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
                 type=click.Choice(tuple(backend.value for backend in ReasoningBackend)),
                 help="Argumentation backend (default: claim_graph)"),
    click.option("--semantics", default="grounded",
                 type=click.Choice(cli_argumentation_semantics_values()),
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


def _parse_revision_atom(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --revision-atom JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise click.ClickException("--revision-atom must decode to a JSON object")
    return parsed


def _parse_revision_conflicts(raw_conflicts: tuple[str, ...]) -> dict[str, list[str]]:
    conflicts: dict[str, list[str]] = {}
    for entry in raw_conflicts:
        atom_id, sep, targets = entry.partition("=")
        if not sep:
            raise click.ClickException(
                "Invalid --revision-conflict; expected atom_id=target[,target...]",
            )
        parsed_targets = [target.strip() for target in targets.split(",") if target.strip()]
        conflicts[str(atom_id)] = parsed_targets
    return conflicts


def _build_revision_dict(
    revision_operation: str | None,
    revision_atom: str | None,
    revision_target: str | None,
    revision_conflicts: tuple[str, ...],
    revision_operator: str | None,
) -> dict[str, Any] | None:
    if revision_operation is None:
        return None

    parsed_atom = _parse_revision_atom(revision_atom)
    parsed_conflicts = _parse_revision_conflicts(revision_conflicts)

    if revision_operation in {"expand", "revise", "iterated_revise"} and parsed_atom is None:
        raise click.ClickException(f"--revision-atom is required for {revision_operation}")
    if revision_operation == "contract" and revision_target is None:
        raise click.ClickException("--revision-target is required for contract")
    if revision_operation == "iterated_revise" and revision_operator is None:
        raise click.ClickException("--revision-operator is required for iterated_revise")

    revision: dict[str, Any] = {
        "operation": revision_operation,
    }
    if parsed_atom is not None:
        revision["atom"] = parsed_atom
    if revision_target is not None:
        revision["target"] = revision_target
    if parsed_conflicts:
        revision["conflicts"] = parsed_conflicts
    if revision_operator is not None:
        revision["operator"] = revision_operator
    return revision


# Import command modules after the group and shared decorators are defined.
from propstore.cli.worldline import display as _display
from propstore.cli.worldline import materialize as _materialize
from propstore.cli.worldline import mutation as _mutation

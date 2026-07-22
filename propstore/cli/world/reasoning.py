"""Reasoning-oriented ``pks world`` command adapters.

``derive`` / ``resolve`` / ``chain`` / ``hypothetical`` over the
:mod:`propstore.world.reasoning_reports` owner tier.
"""

from __future__ import annotations

import json
from typing import Any

import click

from propstore.app.rendering import AppRenderPolicyRequest
from propstore.cli.helpers import CliContext, fail
from propstore.cli.output import emit, emit_table
from propstore.cli.world import (
    build_policy,
    emit_report_json,
    format_option,
    is_json_array,
    is_json_object,
    lifecycle_options,
    lifecycle_policy,
    open_world,
    parse_world_binding_args,
    world,
    world_repo,
)
from propstore.world.reasoning_reports import (
    WorldChainRequest,
    WorldDeriveRequest,
    WorldHypotheticalReport,
    WorldHypotheticalRequest,
    WorldHypotheticalSyntheticClaimSpec,
    WorldResolveError,
    WorldResolveRequest,
    derive_world_value,
    diff_hypothetical_world,
    query_world_chain,
    resolve_world_value,
)


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@lifecycle_options
@format_option
@click.pass_obj
def world_derive(
    obj: CliContext,
    concept_id: str,
    args: tuple[str, ...],
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Derive a value for a concept via its parameterization.

    Usage: ``pks world derive concept5 domain=example``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        report = derive_world_value(
            world_query,
            WorldDeriveRequest(concept_id=concept_id, bindings=bindings, policy=policy),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    emit(f"{report.concept_id}: {report.status}")
    if report.value is not None:
        emit(f"  value: {report.value}")
    if report.formula:
        emit(f"  formula: {report.formula}")
    if report.input_values:
        emit(f"  inputs: {report.input_values}")
    if report.exactness:
        emit(f"  exactness: {report.exactness}")


@world.command("resolve")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option(
    "--strategy",
    required=True,
    type=click.Choice(["recency", "sample_size", "argumentation", "override"]),
)
@click.option(
    "--semantics",
    default="grounded",
    type=click.Choice(["grounded", "preferred", "stable"]),
    help="Argumentation semantics (default: grounded).",
)
@click.option(
    "--set-comparison",
    "set_comparison",
    default="elitist",
    type=click.Choice(["elitist", "democratic"]),
    help="Set comparison for preference ordering (default: elitist).",
)
@click.option(
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
    help="Decision criterion for opinion interpretation (default: pignistic).",
)
@click.option(
    "--pessimism-index",
    "pessimism_index",
    default=0.5,
    type=float,
    help="Hurwicz pessimism index in [0,1] (default: 0.5).",
)
@click.option(
    "--reasoning-backend",
    "reasoning_backend",
    default="claim_graph",
    type=click.Choice(["claim_graph", "aspic", "atms", "praf"]),
    help="Argumentation backend (default: claim_graph).",
)
@click.option(
    "--praf-strategy",
    "praf_strategy",
    default="auto",
    type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
    help="PrAF computation strategy (default: auto).",
)
@click.option("--praf-epsilon", "praf_epsilon", default=0.01, type=float)
@click.option("--praf-confidence", "praf_confidence", default=0.95, type=float)
@click.option("--praf-seed", "praf_seed", default=None, type=int)
@lifecycle_options
@format_option
@click.pass_obj
def world_resolve(
    obj: CliContext,
    concept_id: str,
    args: tuple[str, ...],
    strategy: str,
    semantics: str,
    set_comparison: str,
    decision_criterion: str,
    pessimism_index: float,
    reasoning_backend: str,
    praf_strategy: str,
    praf_epsilon: float,
    praf_confidence: float,
    praf_seed: int | None,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Resolve a (possibly conflicted) concept under a render policy.

    Usage: ``pks world resolve concept1 domain=example --strategy argumentation``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    policy = build_policy(
        AppRenderPolicyRequest(
            reasoning_backend=reasoning_backend,
            strategy=strategy,
            semantics=semantics,
            set_comparison=set_comparison,
            decision_criterion=decision_criterion,
            pessimism_index=pessimism_index,
            praf_strategy=praf_strategy,
            praf_epsilon=praf_epsilon,
            praf_confidence=praf_confidence,
            praf_seed=praf_seed,
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )
    )
    with open_world(repo) as world_query:
        try:
            report = resolve_world_value(
                world_query,
                WorldResolveRequest(
                    concept_id=concept_id, bindings=bindings, policy=policy
                ),
            )
        except WorldResolveError as exc:
            fail(str(exc))

    if fmt == "json":
        emit_report_json(report)
        return
    emit(f"{report.concept_display_id}: {report.status}")
    if report.value is not None:
        emit(f"  value: {report.value}")
    if report.winning_claim_display_id:
        emit(f"  winner: {report.winning_claim_display_id}")
    if report.strategy:
        emit(f"  strategy: {report.strategy}")
    if report.reason:
        emit(f"  reason: {report.reason}")
    if report.acceptance_probs:
        emit("  acceptance_probs:")
        emit_table(
            ("Claim", "Probability"),
            [
                (line.claim_id, f"{line.probability:.4f}")
                for line in report.acceptance_probs
            ],
            indent="    ",
        )


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option(
    "--strategy",
    default=None,
    type=click.Choice(["recency", "sample_size", "argumentation", "override"]),
)
@format_option
@click.pass_obj
def world_chain(
    obj: CliContext,
    concept_id: str,
    args: tuple[str, ...],
    strategy: str | None,
    fmt: str,
) -> None:
    """Backward-chain a target concept through its parameterization graph.

    Usage: ``pks world chain concept5 domain=example --strategy sample_size``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = query_world_chain(
            world_query,
            WorldChainRequest(
                concept_id=concept_id, bindings=bindings, strategy=strategy
            ),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    emit(
        f"Target: {_format_chain_concept(report.target.display_id, report.target.canonical_name)}"
    )
    emit(f"Result: {report.status}")
    if report.value is not None:
        emit(f"  value: {report.value}")
    emit(f"Steps ({len(report.steps)}):")
    for step in report.steps:
        emit(
            f"  {_format_chain_concept(step.concept.display_id, step.concept.canonical_name)}: "
            f"{step.value} ({step.source})"
        )


def _format_chain_concept(display_id: str, canonical_name: str | None) -> str:
    if canonical_name:
        return f"{display_id} ({canonical_name})"
    return display_id


@world.command("hypothetical")
@click.argument("args", nargs=-1)
@click.option("--remove", "remove", multiple=True, help="Claim id to remove.")
@click.option("--add", "add_json", default=None, help="JSON synthetic claim(s).")
@format_option
@click.pass_obj
def world_hypothetical(
    obj: CliContext,
    args: tuple[str, ...],
    remove: tuple[str, ...],
    add_json: str | None,
    fmt: str,
) -> None:
    """Show what changes if claims are removed / added (overlay, not intervention).

    Usage: ``pks world hypothetical domain=example --remove claim2``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = diff_hypothetical_world(
            world_query,
            WorldHypotheticalRequest(
                bindings=bindings,
                remove_claim_ids=tuple(remove),
                add_claims=_parse_hypothetical_add(add_json),
            ),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    _render_hypothetical_text(report)


def _parse_hypothetical_add(
    add_json: str | None,
) -> tuple[WorldHypotheticalSyntheticClaimSpec, ...]:
    if add_json is None:
        return ()
    try:
        raw = json.loads(add_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"invalid --add JSON: {exc}") from exc
    candidates: list[Any]
    if is_json_array(raw):
        candidates = list(raw)
    elif is_json_object(raw):
        candidates = [raw]
    else:
        raise click.ClickException("--add JSON must be an object or a list of objects")
    return tuple(_spec_from_entry(entry) for entry in candidates)


def _spec_from_entry(entry: object) -> WorldHypotheticalSyntheticClaimSpec:
    if not is_json_object(entry):
        raise click.ClickException("--add JSON entries must be objects")
    claim_id = entry.get("id")
    concept_id = entry.get("concept_id")
    if not isinstance(claim_id, str) or not claim_id:
        raise click.ClickException("--add JSON entries require a string id")
    if not isinstance(concept_id, str) or not concept_id:
        raise click.ClickException("--add JSON entries require a string concept_id")
    conditions = entry.get("conditions", [])
    if not is_json_array(conditions):
        raise click.ClickException("--add JSON conditions must be a list")
    claim_type = entry.get("type", "parameter")
    if not isinstance(claim_type, str):
        raise click.ClickException("--add JSON type must be a string")
    value = entry.get("value")
    if value is not None and not isinstance(value, str | bool | int | float):
        raise click.ClickException("--add JSON value must be a scalar")
    return WorldHypotheticalSyntheticClaimSpec(
        claim_id=claim_id,
        concept_id=concept_id,
        claim_type=claim_type,
        value=value,
        conditions=tuple(str(condition) for condition in conditions),
    )


def _render_hypothetical_text(report: WorldHypotheticalReport) -> None:
    extension_diff = report.extension_diff
    before = _extension_counts_text(
        extension_diff.before.accepted,
        extension_diff.before.defeated,
        extension_diff.before.undecided,
    )
    after = _extension_counts_text(
        extension_diff.after.accepted,
        extension_diff.after.defeated,
        extension_diff.after.undecided,
    )
    if extension_diff.unchanged:
        emit(f"Extension unchanged ({after}; same fixed point)")
    else:
        emit(f"Extension changed (before: {before}; after: {after})")
        for transition in extension_diff.transitions:
            emit(
                f"  {transition.from_status} -> {transition.to_status} "
                f"({len(transition.claim_ids)}): " + ", ".join(transition.claim_ids)
            )

    if not report.changes:
        emit("Value diff: unchanged")
        return
    emit("Value diff:")
    for change in report.changes:
        emit(
            f"  {change.concept_display_id}: "
            f"{change.base_status} -> {change.hypothetical_status}"
        )


def _extension_counts_text(accepted: int, defeated: int, undecided: int) -> str:
    return f"{accepted} accepted / {defeated} defeated / {undecided} undecided"

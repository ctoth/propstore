"""Analysis-oriented ``pks world`` command adapters.

``sensitivity`` (:func:`propstore.sensitivity.query_sensitivity`),
``check-consistency`` (:func:`propstore.world.consistency.check_world_consistency`),
and ``fragility`` (:func:`propstore.fragility.query_fragility`). The consistency
and fragility owners take a :class:`~propstore.core.environment.WorldStore`; a
:class:`~propstore.world.WorldQuery` is one, so it is passed directly.
"""
from __future__ import annotations

import click

from propstore.cli.helpers import CliContext
from propstore.cli.output import emit, emit_table
from propstore.cli.world import (
    emit_report_json,
    format_option,
    open_world,
    parse_world_binding_args,
    world,
    world_repo,
)
from propstore.fragility import FragilityRequest, query_fragility
from propstore.sensitivity import SensitivityRequest, query_sensitivity
from propstore.world.consistency import (
    WorldConsistencyRequest,
    check_world_consistency,
)


@world.command("sensitivity")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@format_option
@click.pass_obj
def world_sensitivity(
    obj: CliContext,
    concept_id: str,
    args: tuple[str, ...],
    fmt: str,
) -> None:
    """Analyze which input most influences a derived quantity.

    Usage: ``pks world sensitivity concept5 domain=example``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = query_sensitivity(
            world_query, SensitivityRequest(concept_id=concept_id, bindings=bindings)
        )

    if fmt == "json":
        emit_report_json(report)
        return
    result = report.result
    if result is None:
        emit(f"No sensitivity analysis available for {report.concept_id}.")
        return
    emit(f"Sensitivity: {report.concept_id}")
    emit(f"Formula: {result.formula}")
    emit(f"Output value: {result.output_value}")
    emit(f"Inputs: {result.input_values}")
    emit("")
    emit_table(
        ("Input", "Partial", "Elasticity"),
        [
            (
                str(entry.input_concept_id),
                "N/A"
                if entry.partial_derivative_value is None
                else f"{entry.partial_derivative_value:.6g}",
                "N/A" if entry.elasticity is None else f"{entry.elasticity:.4f}",
            )
            for entry in result.entries
        ],
    )


@world.command("check-consistency")
@click.argument("args", nargs=-1)
@click.option(
    "--transitive", is_flag=True, help="Check multi-hop transitive conflicts."
)
@format_option
@click.pass_obj
def world_check_consistency(
    obj: CliContext,
    args: tuple[str, ...],
    transitive: bool,
    fmt: str,
) -> None:
    """Check for conflicts, optionally including transitive (multi-hop) ones.

    Usage: ``pks world check-consistency domain=example [--transitive]``.
    """

    repo = world_repo(obj)
    bindings, _ = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = check_world_consistency(
            world_query,
            WorldConsistencyRequest(bindings=bindings, transitive=transitive),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    if report.transitive:
        if not report.conflicts:
            emit("No transitive conflicts found.")
            return
        emit(f"Found {len(report.conflicts)} transitive conflict(s):")
        for conflict in report.conflicts:
            emit(f"  {conflict.concept_id}: {conflict.value_a} vs {conflict.value_b}")
            if conflict.derivation_chain:
                emit(f"    chain: {conflict.derivation_chain}")
        return

    if not report.conflicts:
        emit("No conflicts under current bindings.")
        return
    emit(f"Found {len(report.conflicts)} conflict(s):")
    for conflict in report.conflicts:
        emit(
            f"  {conflict.concept_id}: {conflict.warning_class} "
            f"({conflict.claim_a_id} vs {conflict.claim_b_id})"
        )


@world.command("fragility")
@click.argument("args", nargs=-1)
@click.option("--concept", "concept_id", default=None, help="Focus on one concept.")
@click.option("--top-k", "top_k", type=int, default=20, help="Number of results.")
@click.option("--skip-atms", is_flag=True, default=False)
@click.option("--skip-discovery", is_flag=True, default=False)
@click.option("--skip-conflict", is_flag=True, default=False)
@click.option("--skip-grounding", is_flag=True, default=False)
@click.option("--skip-bridge", is_flag=True, default=False)
@click.option(
    "--ranking-policy",
    "ranking_policy",
    type=click.Choice(["heuristic_roi", "family_local_only", "pareto"]),
    default="heuristic_roi",
)
@format_option
@click.pass_obj
def world_fragility(
    obj: CliContext,
    args: tuple[str, ...],
    concept_id: str | None,
    top_k: int,
    skip_atms: bool,
    skip_discovery: bool,
    skip_conflict: bool,
    skip_grounding: bool,
    skip_bridge: bool,
    ranking_policy: str,
    fmt: str,
) -> None:
    """Rank intervention targets by fragility — what to inspect next."""

    repo = world_repo(obj)
    bindings, context_id = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = query_fragility(
            world_query,
            FragilityRequest(
                bindings=bindings,
                context_id=context_id,
                concept_id=concept_id,
                top_k=top_k,
                include_atms=not skip_atms,
                include_discovery=not skip_discovery,
                include_conflict=not skip_conflict,
                include_grounding=not skip_grounding,
                include_bridge=not skip_bridge,
                ranking_policy=ranking_policy,
            ),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    emit(f"Fragility Analysis (top {top_k}, ranking={ranking_policy})")
    emit("=" * 60)
    emit("")
    emit_table(
        ("Rank", "Score", "ROI", "Cost", "Family", "Kind", "Intervention"),
        [
            (
                index,
                f"{item.local_fragility:.2f}",
                f"{item.roi:.2f}",
                item.target.cost_tier,
                item.target.family,
                item.target.kind,
                item.target.intervention_id,
            )
            for index, item in enumerate(report.interventions, 1)
        ],
        show_header_when_empty=True,
    )
    emit("")
    emit(f"World fragility: {report.world_fragility:.2f}")
    if report.interactions:
        emit("")
        emit("Interactions:")
        for interaction in report.interactions:
            concepts = interaction.subjects_affected
            concept_str = f" for {', '.join(concepts)}" if concepts else ""
            emit(
                f"  {interaction.intervention_a_id} + "
                f"{interaction.intervention_b_id}: "
                f"{interaction.interaction_type}{concept_str}"
            )

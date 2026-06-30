"""Basic ``pks world`` query command adapters.

``status`` / ``query`` / ``bind`` / ``explain`` / ``algorithms`` over the
:mod:`propstore.world.reasoning_reports` owner tier. ``world_status`` is also the
synthetic root ``pks status`` command (the lazy registry maps ``status`` here).
"""
from __future__ import annotations

import click

from propstore.cli.helpers import CliContext, fail
from propstore.cli.output import emit, emit_table
from propstore.cli.world import (
    emit_report_json,
    format_option,
    lifecycle_options,
    lifecycle_policy,
    open_world,
    parse_world_binding_args,
    world,
    world_repo,
)
from propstore.world.reasoning_reports import (
    UnknownClaimError,
    UnknownConceptError,
    WorldAlgorithmsRequest,
    WorldBindActiveReport,
    WorldBindConceptReport,
    WorldBindRequest,
    WorldConceptQueryRequest,
    WorldExplainRequest,
    WorldStatusRequest,
    explain_world_claim,
    get_world_status,
    list_world_algorithms,
    query_bound_world,
    query_world_concept,
)


@world.command("status")
@lifecycle_options
@format_option
@click.pass_obj
def world_status(
    obj: CliContext,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Show knowledge-base counts under the lifecycle-visibility policy."""

    repo = world_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        report = get_world_status(world_query, WorldStatusRequest(policy=policy))

    if fmt == "json":
        emit_report_json(report)
        return
    emit(f"Concepts:           {report.concept_count}")
    emit(f"Claims:             {report.visible_claim_count}")
    emit(f"Conflict witnesses: {report.conflict_count}")
    emit(f"Stances:            {report.stance_count}")
    if show_quarantined:
        emit(f"Diagnostics:        {report.diagnostic_count}")


@world.command("query")
@click.argument("concept_id")
@lifecycle_options
@format_option
@click.pass_obj
def world_query(
    obj: CliContext,
    concept_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Show all claims for a concept under the lifecycle-visibility policy."""

    repo = world_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        try:
            report = query_world_concept(
                world_query,
                WorldConceptQueryRequest(target=concept_id, policy=policy),
            )
        except UnknownConceptError:
            fail(f"Unknown concept: {concept_id}")

    if fmt == "json":
        emit_report_json(report)
        return
    emit(f"{report.canonical_name} ({report.concept_display_id})")
    if not report.claims:
        emit("  (no claims)")
    for claim in report.claims:
        emit(
            f"  {claim.display_id}: {claim.claim_type} "
            f"{claim.value_display} conditions={claim.conditions}"
        )
    if show_quarantined and report.diagnostics:
        emit("Diagnostics:")
        for diagnostic in report.diagnostics:
            emit(
                f"  {diagnostic.target} "
                f"[{diagnostic.diagnostic_kind}] {diagnostic.message}"
            )


@world.command("bind")
@click.argument("args", nargs=-1)
@format_option
@click.pass_obj
def world_bind(obj: CliContext, args: tuple[str, ...], fmt: str) -> None:
    """Show active claims under condition bindings.

    Usage: ``pks world bind domain=example [concept_id]`` — tokens with ``=`` are
    bindings; a trailing token without ``=`` is a concept filter.
    """

    repo = world_repo(obj)
    bindings, target = parse_world_binding_args(args)
    with open_world(repo) as world_query:
        report = query_bound_world(
            world_query,
            WorldBindRequest(bindings=bindings, target=target),
        )

    if fmt == "json":
        emit_report_json(report)
        return
    if isinstance(report, WorldBindConceptReport):
        emit(f"{report.concept_display_id}: {report.status}")
        for claim in report.claims:
            emit(f"  {claim.display_id}: {claim.value_display}")
        return

    assert isinstance(report, WorldBindActiveReport)
    emit(f"Active claims: {report.active_claim_count}")
    for claim in report.claims:
        emit(
            f"  {claim.display_id}: {claim.concept_display_id} "
            f"{claim.value_display} conditions={claim.conditions}"
        )


@world.command("explain")
@click.argument("claim_id")
@format_option
@click.pass_obj
def world_explain(obj: CliContext, claim_id: str, fmt: str) -> None:
    """Show the stance chain incident to a claim."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        try:
            report = explain_world_claim(
                world_query, WorldExplainRequest(claim_id=claim_id)
            )
        except UnknownClaimError:
            fail(f"Unknown claim: {claim_id}")

    if fmt == "json":
        emit_report_json(report)
        return
    emit(
        f"{report.claim_display_id}: {report.claim_type} "
        f"concept={report.concept_display_id} value={report.value}"
    )
    if not report.stances:
        emit("  (no stances)")
    for stance in report.stances:
        indent = "    " if stance.nested else "  "
        emit(
            f"{indent}{stance.source_display_id} {stance.stance_type} -> "
            f"{stance.target_display_id} (confidence={stance.confidence})"
        )


@world.command("algorithms")
@click.option("--concept", default=None, help="Filter by focus concept.")
@format_option
@click.pass_obj
def world_algorithms(
    obj: CliContext,
    concept: str | None,
    fmt: str,
) -> None:
    """List algorithm claims in the world model."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        report = list_world_algorithms(
            world_query, WorldAlgorithmsRequest(concept=concept)
        )

    if fmt == "json":
        emit_report_json(report)
        return
    if not report.algorithms:
        emit("No algorithm claims found.")
        return
    emit_table(
        ("ID", "Name", "Concept"),
        [
            (claim.claim_id, claim.name, claim.concept_id)
            for claim in report.algorithms
        ],
    )
    emit(f"\n{len(report.algorithms)} algorithm claim(s).")

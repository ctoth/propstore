"""ATMS-oriented ``pks world`` command adapters."""
from __future__ import annotations

import click

from propstore.cli.helpers import exit_with_code
from propstore.cli.output import emit, emit_section

from propstore.app.world_atms import (
    AppAtmsInterventionRequest,
    AppAtmsTargetRequest,
    AppAtmsViewRequest,
    AtmsClaimFutureReport,
    AtmsClaimWhyOutReport,
    AtmsConceptFutureReport,
    AtmsConceptWhyOutReport,
    WorldAtmsValidationError,
    world_atms_context,
    world_atms_futures,
    world_atms_interventions,
    world_atms_next_query,
    world_atms_relevance,
    world_atms_stability,
    world_atms_status,
    world_atms_verify,
    world_atms_why_out,
)
from propstore.cli.world import (
    _format_assumption_ids,
    parse_world_binding_args,
    world,
)
from propstore.repository import Repository


@world.group("atms", no_args_is_help=True)
def atms() -> None:
    """Inspect ATMS-backed world state."""


def _view_request(args: tuple[str, ...], context: str | None) -> AppAtmsViewRequest:
    bindings, concept_id = parse_world_binding_args(args)
    return AppAtmsViewRequest(
        bindings=bindings,
        concept_id=concept_id,
        context=context,
    )


@atms.command("status")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_status_command(
    obj: dict,
    args: tuple[str, ...],
    context: str | None,
) -> None:
    """Show ATMS-native claim status, support quality, and essential support."""
    repo: Repository = obj["repo"]
    report = world_atms_status(repo, _view_request(args, context))
    if not report.claims:
        emit("No active claims for the current ATMS view.")
        return

    for claim in report.claims:
        emit(
            f"{claim.claim_id}: status={claim.status} "
            f"support_quality={claim.support_quality} "
            f"essential_support={_format_assumption_ids(claim.essential_support)}"
        )
        emit(f"  reason: {claim.reason}")


@atms.command("context")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_context_command(
    obj: dict,
    args: tuple[str, ...],
    context: str | None,
) -> None:
    """Show which ATMS-supported claims hold in the current bound environment."""
    repo: Repository = obj["repo"]
    report = world_atms_context(repo, _view_request(args, context))
    emit(f"Environment: {_format_assumption_ids(report.environment)}")

    if not report.claims:
        emit("No claims have exact ATMS support in the current environment.")
        return

    for claim in report.claims:
        emit(
            f"{claim.claim_id}: status={claim.status} "
            f"essential_support={_format_assumption_ids(claim.essential_support)}"
        )


@atms.command("verify")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_verify_command(
    obj: dict,
    args: tuple[str, ...],
    context: str | None,
) -> None:
    """Run ATMS label self-checks for the current bound environment."""
    repo: Repository = obj["repo"]
    report = world_atms_verify(repo, _view_request(args, context))
    if report.ok:
        emit("ATMS labels verified.")
        return

    for section_name, errors in report.sections.items():
        if not errors:
            continue
        emit_section(f"{section_name}:", errors)

    exit_with_code(2)


@atms.command("futures")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    required=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_futures_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS future environments for a claim or concept."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = world_atms_futures(
        repo,
        AppAtmsTargetRequest(
            target=target,
            bindings=bindings,
            queryables=queryables,
            limit=limit,
            context=context,
        ),
    )
    if isinstance(report, AtmsClaimFutureReport):
        _render_future_report(report)
        return

    if not report.claims:
        emit("No active claims for the requested ATMS future view.")
        return
    for claim_report in report.claims:
        _render_future_report(claim_report)


@atms.command("why-out")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_why_out_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Explain whether an ATMS OUT status is missing-support or nogood-pruned."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = world_atms_why_out(
        repo,
        AppAtmsTargetRequest(
            target=target,
            bindings=bindings,
            queryables=queryables,
            limit=limit,
            context=context,
        ),
    )
    if isinstance(report, AtmsClaimWhyOutReport):
        emit(
            f"{report.target}: out_kind={report.out_kind} "
            f"future_activatable={report.future_activatable}"
        )
        emit(
            f"  candidate_queryables={_format_assumption_ids(report.candidate_queryables)}"
        )
        emit(f"  reason: {report.reason}")
        return

    emit(
        f"{report.target}: value_status={report.value_status} "
        f"supported_claim_ids={_format_assumption_ids(report.supported_claim_ids)}"
    )
    for claim_report in report.claim_reasons:
        emit(
            f"  {claim_report.target}: out_kind={claim_report.out_kind} "
            f"future_activatable={claim_report.future_activatable}"
        )


@atms.command("stability")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    required=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_stability_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS-native stability over the implemented future replay substrate."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = world_atms_stability(
        repo,
        AppAtmsTargetRequest(
            target=target,
            bindings=bindings,
            queryables=queryables,
            limit=limit,
            context=context,
        ),
    )
    emit(
        f"{report.target}: status={report.current_status} "
        f"stable={report.stable} "
        f"consistent_futures={report.consistent_future_count}"
    )
    if not report.witnesses:
        emit("  no bounded consistent future flips the status")
    emit_section(
        "",
        (
            f"witness [{', '.join(witness.queryable_cels)}] -> {witness.status}"
            for witness in report.witnesses
        ),
    )


@atms.command("relevance")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    required=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_relevance_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show which bounded queryables can flip an ATMS or concept status."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = world_atms_relevance(
        repo,
        AppAtmsTargetRequest(
            target=target,
            bindings=bindings,
            queryables=queryables,
            limit=limit,
            context=context,
        ),
    )
    emit(
        f"{report.target}: current_status={report.current_status} "
        f"relevant_queryables={_format_assumption_ids(report.relevant_queryables)}"
    )
    for pair in report.witness_pairs:
        emit(
            f"  {pair.queryable_cel}: "
            f"[{', '.join(pair.without_queryables)}] -> {pair.without_status}; "
            f"[{', '.join(pair.with_queryables)}] -> {pair.with_status}"
        )


@atms.command("interventions")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    required=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_interventions_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded additive intervention plans for an ATMS claim or concept."""
    repo: Repository = obj["repo"]
    emit("bounded additive plans over declared queryables")
    emit("not revision/contraction")

    try:
        bindings, _ = parse_world_binding_args(args)
        report = world_atms_interventions(
            repo,
            AppAtmsInterventionRequest(
                target=target,
                bindings=bindings,
                target_status=target_status,
                queryables=queryables,
                limit=limit,
                context=context,
            ),
        )
    except WorldAtmsValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    emit_section(
        "",
        (
            f"plan [{', '.join(plan.queryable_cels)}] -> {plan.result_status}"
            for plan in report.plans
        ),
    )


@atms.command("next-query")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option(
    "--queryable",
    "queryables",
    multiple=True,
    required=True,
    help="Future/queryable assumption (CEL or key=value)",
)
@click.option(
    "--limit",
    default=8,
    show_default=True,
    type=int,
    help="Maximum number of future environments to inspect",
)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_next_query_command(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show next-query suggestions derived from bounded additive intervention plans."""
    repo: Repository = obj["repo"]
    emit("derived from bounded additive intervention plans")

    try:
        bindings, _ = parse_world_binding_args(args)
        report = world_atms_next_query(
            repo,
            AppAtmsInterventionRequest(
                target=target,
                bindings=bindings,
                target_status=target_status,
                queryables=queryables,
                limit=limit,
                context=context,
            ),
        )
    except WorldAtmsValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    emit_section(
        "",
        (
            f"{suggestion.queryable_cel}: "
            f"coverage={suggestion.plan_count} "
            f"smallest_plan_size={suggestion.smallest_plan_size}"
            for suggestion in report.suggestions
        ),
    )


def _render_future_report(report: AtmsClaimFutureReport) -> None:
    emit(
        f"{report.target}: current_status={report.current_status} "
        f"could_become_in={report.could_become_in} "
        f"could_become_out={report.could_become_out}"
    )
    emit_section(
        "",
        (
            f"future [{', '.join(future.queryable_cels)}] -> {future.status}"
            for future in report.futures
        ),
    )

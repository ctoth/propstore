"""ATMS-oriented ``pks world`` command adapters."""
from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
import sys
from typing import TYPE_CHECKING

import click

from propstore.cli.helpers import open_world_model
from propstore.cli.world import (
    _format_assumption_ids,
    _parse_bindings,
    _resolve_world_target,
    world,
)
from propstore.repository import Repository
from propstore.world.types import ATMSNodeStatus, coerce_value_status

if TYPE_CHECKING:
    from propstore.world import QueryableAssumption


@world.group("atms", no_args_is_help=True)
def atms() -> None:
    """Inspect ATMS-backed world state."""


@contextmanager
def _open_atms_world(
    repo: Repository,
    args: tuple[str, ...],
    *,
    context: str | None = None,
):
    from propstore.world.atms_workflows import ATMSBindRequest, bind_atms_world

    with open_world_model(repo) as wm:
        bindings, concept_id = _parse_bindings(args)
        bound = bind_atms_world(wm, ATMSBindRequest(bindings, context))
        yield wm, bound, bindings, concept_id


def _parse_queryables(
    queryables: tuple[str, ...],
) -> list[QueryableAssumption]:
    from propstore.world.types import coerce_queryable_assumptions

    return list(coerce_queryable_assumptions(queryables))


def _format_status_value(status: object) -> str:
    if isinstance(status, str):
        return status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


@atms.command("status")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_status(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show ATMS-native claim status, support quality, and essential support."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, concept_id):
        resolved = None
        if concept_id:
            resolved = _resolve_world_target(wm, concept_id)
        active_claims = sorted(bound.active_claims(resolved), key=lambda claim: str(claim.claim_id))
        if not active_claims:
            click.echo("No active claims for the current ATMS view.")
            return

        for claim in active_claims:
            inspection = bound.claim_status(str(claim.claim_id))
            click.echo(
                f"{claim.claim_id}: status={inspection.status.value} "
                f"support_quality={inspection.support_quality.value} "
                f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
            )
            click.echo(f"  reason: {inspection.reason}")


@atms.command("context")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_context(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show which ATMS-supported claims hold in the current bound environment."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, concept_id):
        environment_key = tuple(
            assumption.assumption_id
            for assumption in bound._environment.assumptions
        )
        click.echo(f"Environment: {_format_assumption_ids(environment_key)}")

        claim_ids = bound.claims_in_environment(environment_key)
        if concept_id:
            resolved = _resolve_world_target(wm, concept_id)
            allowed = {
                str(claim.claim_id)
                for claim in bound.active_claims(resolved)
            }
            claim_ids = [claim_id for claim_id in claim_ids if claim_id in allowed]

        if not claim_ids:
            click.echo("No claims have exact ATMS support in the current environment.")
            return

        for claim_id in sorted(claim_ids):
            inspection = bound.claim_status(claim_id)
            click.echo(
                f"{claim_id}: status={inspection.status.value} "
                f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
            )


@atms.command("verify")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_verify(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Run ATMS label self-checks for the current bound environment."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (_wm, bound, _bindings, _concept_id):
        report = bound.atms_engine().verify_labels()
        if report["ok"]:
            click.echo("ATMS labels verified.")
            return

        for section in (
            "consistency_errors",
            "minimality_errors",
            "soundness_errors",
            "completeness_errors",
        ):
            errors = report.get(section) or []
            if not errors:
                continue
            click.echo(f"{section}:")
            for error in errors:
                click.echo(f"  {error}")

    sys.exit(2)


@atms.command("futures")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_futures(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS future environments for a claim or concept."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_future_statuses(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: current_status={report['current'].status.value} "
                f"could_become_in={report['could_become_in']} "
                f"could_become_out={report['could_become_out']}"
            )
            for future in report["futures"]:
                click.echo(
                    f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        concept_report = bound.concept_future_statuses(resolved, parsed_queryables, limit=limit)
        if not concept_report:
            click.echo("No active claims for the requested ATMS future view.")
            return
        for claim_id in sorted(concept_report):
            report = concept_report[claim_id]
            click.echo(
                f"{claim_id}: current_status={report['current'].status.value} "
                f"could_become_in={report['could_become_in']} "
                f"could_become_out={report['could_become_out']}"
            )
            for future in report["futures"]:
                click.echo(
                    f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
                )


@atms.command("why-out")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_why_out(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Explain whether an ATMS OUT status is missing-support or nogood-pruned."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.atms_engine().why_out(
                f"claim:{target}",
                queryables=parsed_queryables,
                limit=limit,
            )
            click.echo(
                f"{target}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
                f"future_activatable={report['future_activatable']}"
            )
            click.echo(
                f"  candidate_queryables={_format_assumption_ids([', '.join(item) for item in report['candidate_queryable_cels']])}"
            )
            click.echo(f"  reason: {report['reason']}")
            return

        resolved = _resolve_world_target(wm, target)
        concept_report = bound.why_concept_out(resolved, parsed_queryables, limit=limit)
        click.echo(
                f"{resolved}: value_status={concept_report['value_status']} "
                f"supported_claim_ids={_format_assumption_ids(concept_report['supported_claim_ids'])}"
            )
        for claim_id, report in sorted(concept_report["claim_reasons"].items()):
            click.echo(
                f"  {claim_id}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
                f"future_activatable={report['future_activatable']}"
            )


@atms.command("stability")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_stability(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS-native stability over the implemented future replay substrate."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_stability(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: status={report['current'].status.value} "
                f"stable={report['stable']} "
                f"consistent_futures={report['consistent_future_count']}"
            )
            if not report["witnesses"]:
                click.echo("  no bounded consistent future flips the status")
            for witness in report["witnesses"]:
                click.echo(
                    f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status'].value}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        report = bound.concept_stability(resolved, parsed_queryables, limit=limit)
        click.echo(
            f"{resolved}: value_status={report['current_status']} "
            f"stable={report['stable']} "
            f"consistent_futures={report['consistent_future_count']}"
        )
        if not report["witnesses"]:
            click.echo("  no bounded consistent future flips the value status")
        for witness in report["witnesses"]:
            click.echo(
                f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status']}"
            )


@atms.command("relevance")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_relevance(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show which bounded queryables can flip an ATMS or concept status."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_relevance(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: current_status={report['current'].status.value} "
                f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
            )
            for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
                for pair in pairs:
                    click.echo(
                        f"  {queryable_cel}: "
                        f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status'].value}; "
                        f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status'].value}"
                    )
            return

        resolved = _resolve_world_target(wm, target)
        report = bound.concept_relevance(resolved, parsed_queryables, limit=limit)
        click.echo(
            f"{resolved}: current_status={report['current_status']} "
            f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
        )
        for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
            for pair in pairs:
                click.echo(
                    f"  {queryable_cel}: "
                    f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status']}; "
                    f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status']}"
                )


@atms.command("interventions")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_interventions(
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
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        click.echo("bounded additive plans over declared queryables")
        click.echo("not revision/contraction")

        claim = wm.get_claim(target)
        if claim is not None:
            try:
                typed_target_status = ATMSNodeStatus(target_status)
            except ValueError as exc:
                raise click.ClickException(str(exc)) from exc
            plans = bound.claim_interventions(
                target,
                parsed_queryables,
                typed_target_status,
                limit=limit,
            )
            for plan in plans:
                status_val = _format_status_value(plan["result_status"])
                click.echo(
                    f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        try:
            typed_target_status = coerce_value_status(target_status)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if typed_target_status is None:
            raise click.ClickException("target status is required")
        plans = bound.concept_interventions(
            resolved,
            parsed_queryables,
            typed_target_status,
            limit=limit,
        )
        for plan in plans:
            status_val = _format_status_value(plan["result_status"])
            click.echo(
                f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
            )


@atms.command("next-query")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_next_query(
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
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        click.echo("derived from bounded additive intervention plans")

        claim = wm.get_claim(target)
        if claim is not None:
            try:
                typed_target_status = ATMSNodeStatus(target_status)
            except ValueError as exc:
                raise click.ClickException(str(exc)) from exc
            suggestions = bound.claim_next_queryables(
                target,
                parsed_queryables,
                typed_target_status,
                limit=limit,
            )
            for suggestion in suggestions:
                click.echo(
                    f"  {suggestion['queryable_cel']}: "
                    f"coverage={suggestion['plan_count']} "
                    f"smallest_plan_size={suggestion['smallest_plan_size']}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        try:
            typed_target_status = coerce_value_status(target_status)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if typed_target_status is None:
            raise click.ClickException("target status is required")
        suggestions = bound.concept_next_queryables(
            resolved,
            parsed_queryables,
            typed_target_status,
            limit=limit,
        )
        for suggestion in suggestions:
            click.echo(
                f"  {suggestion['queryable_cel']}: "
                f"coverage={suggestion['plan_count']} "
                f"smallest_plan_size={suggestion['smallest_plan_size']}"
            )

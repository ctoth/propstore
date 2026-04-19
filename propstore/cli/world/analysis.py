"""Analysis-oriented ``pks world`` command adapters."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import click

from propstore.app.world import (
    WorldLifecycleOptions,
    lifecycle_policy,
    open_app_world_model,
    parse_world_binding_args,
)
from propstore.cli.world import world
from propstore.repository import Repository


def _parse_hypothetical_add(add_json: str | None):
    """Parse the CLI JSON payload for ``world hypothetical --add``."""
    from propstore.world.queries import WorldHypotheticalSyntheticClaimSpec

    if add_json is None:
        return ()
    try:
        raw = json.loads(add_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"invalid --add JSON: {exc.msg}") from exc
    entries = [raw] if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise click.ClickException("--add JSON must be an object or a list of objects")
    specs: list[WorldHypotheticalSyntheticClaimSpec] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise click.ClickException("--add JSON entries must be objects")
        claim_id = entry.get("id")
        concept_id = entry.get("concept_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise click.ClickException("--add JSON entries require string id")
        if not isinstance(concept_id, str) or not concept_id:
            raise click.ClickException("--add JSON entries require string concept_id")
        conditions = entry.get("conditions", [])
        if not isinstance(conditions, list):
            raise click.ClickException("--add JSON conditions must be a list")
        value = entry.get("value")
        if value is not None and (
            not isinstance(value, str | int | float) or isinstance(value, bool)
        ):
            raise click.ClickException("--add JSON value must be a string or number")
        specs.append(
            WorldHypotheticalSyntheticClaimSpec(
                claim_id=claim_id,
                concept_id=concept_id,
                claim_type=entry.get("type", "parameter"),
                value=float(value) if isinstance(value, int | float) else value,
                conditions=tuple(conditions),
            )
        )
    return tuple(specs)


def _format_chain_concept(concept) -> str:
    if concept.canonical_name:
        return f"{concept.display_id} ({concept.canonical_name})"
    return str(concept.display_id)


@world.command("hypothetical")
@click.argument("args", nargs=-1)
@click.option("--remove", multiple=True, help="Claim ID to remove")
@click.option("--add", "add_json", default=None, help="JSON synthetic claim")
@click.pass_obj
def world_hypothetical(obj: dict, args: tuple[str, ...],
                       remove: tuple[str, ...], add_json: str | None) -> None:
    """Show what changes if claims are removed/added.

    Usage: pks world hypothetical domain=example --remove claim2
    """
    from propstore.world.queries import (
        WorldHypotheticalRequest,
        diff_hypothetical_world,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = diff_hypothetical_world(
            wm,
            WorldHypotheticalRequest(
                bindings=bindings,
                remove_claim_ids=tuple(remove),
                add_claims=_parse_hypothetical_add(add_json),
            ),
        )

    if not report.changes:
        click.echo("No changes detected.")
    else:
        for change in report.changes:
            click.echo(
                f"{change.concept_display_id}: "
                f"{change.base_status} → {change.hypothetical_status}"
            )


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", default=None,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' during chain traversal.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' during chain traversal."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to inform chain output.",
)
@click.pass_obj
def world_chain(obj: dict, concept_id: str, args: tuple[str, ...],
                strategy: str | None,
                include_drafts: bool,
                include_blocked: bool,
                show_quarantined: bool) -> None:
    """Traverse the parameter space to derive a target concept.

    Lifecycle-visibility flags are accepted and layered onto any
    strategy-derived policy per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    (axis-1 findings 3.1 / 3.2 / 3.3).

    Usage: pks world chain concept5 domain=example --strategy sample_size
    """
    from propstore.world.queries import WorldChainRequest, query_world_chain

    # The flags do not change the chain traversal shape today — chain_query
    # reads parameterization + relationship state, not lifecycle-filtered
    # claim sets. The flags are accepted here so users can pipe the same
    # invocation across `pks world ...` subcommands without per-subcommand
    # option divergence; build/render-time policy work already applies at
    # the store layer via ``WorldModel.claims_with_policy``. When a
    # future chain implementation threads a ``RenderPolicy``, this helper
    # remains the construction site.
    _ = lifecycle_policy(
        WorldLifecycleOptions(
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = query_world_chain(
            wm,
            WorldChainRequest(
                concept_id=concept_id,
                bindings=bindings,
                strategy=strategy,
            ),
        )

    click.echo(f"Target: {_format_chain_concept(report.target)}")
    click.echo(f"Result: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    click.echo(f"Steps ({len(report.steps)}):")
    for step in report.steps:
        click.echo(
            f"  {_format_chain_concept(step.concept)}: {step.value} ({step.source})"
        )


@world.command("export-graph")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["dot", "json"]), default="dot")
@click.option("--group", "group_id", type=int, default=None,
              help="Parameterization group ID to filter by")
@click.option("--output", "output_file", default=None, help="Output file path")
@click.pass_obj
def world_export_graph(obj: dict, args: tuple[str, ...], fmt: str,
                       group_id: int | None, output_file: str | None) -> None:
    """Export the knowledge graph as DOT or JSON.

    Usage: pks world export-graph domain=example --format dot --output graph.dot
    """
    from propstore.graph_export import GraphExportRequest, export_knowledge_graph

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = export_knowledge_graph(
            wm,
            GraphExportRequest(bindings=bindings, group_id=group_id),
        )

    if fmt == "json":
        output = json.dumps(report.graph.to_json(), indent=2)
    else:
        output = report.graph.to_dot()

    if output_file:
        Path(output_file).write_text(output)
        click.echo(f"Graph written to {output_file}")
    else:
        click.echo(output)


@world.command("sensitivity")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_sensitivity(obj: dict, concept_id: str, args: tuple[str, ...],
                      fmt: str) -> None:
    """Analyze which input most influences a derived quantity.

    Usage: pks world sensitivity concept5 domain=example
    """
    from propstore.sensitivity import SensitivityRequest, query_sensitivity

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = query_sensitivity(
            wm,
            SensitivityRequest(concept_id=concept_id, bindings=bindings),
        )
        result = report.result

    if result is None:
        click.echo(f"No sensitivity analysis available for {report.concept_id}.")
        return

    if fmt == "json":
        data = {
            "concept_id": result.concept_id,
            "formula": result.formula,
            "output_value": result.output_value,
            "input_values": result.input_values,
            "entries": [
                {
                    "input_concept_id": e.input_concept_id,
                    "partial_derivative_expr": e.partial_derivative_expr,
                    "partial_derivative_value": e.partial_derivative_value,
                    "elasticity": e.elasticity,
                }
                for e in result.entries
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Sensitivity: {report.concept_id}")
        click.echo(f"Formula: {result.formula}")
        click.echo(f"Output value: {result.output_value}")
        click.echo(f"Inputs: {result.input_values}")
        click.echo("")
        click.echo(f"{'Input':<25} {'Partial':>12} {'Elasticity':>12}")
        click.echo("-" * 51)
        for e in result.entries:
            pval = f"{e.partial_derivative_value:.6g}" if e.partial_derivative_value is not None else "N/A"
            elast = f"{e.elasticity:.4f}" if e.elasticity is not None else "N/A"
            click.echo(f"{e.input_concept_id:<25} {pval:>12} {elast:>12}")


@world.command("fragility")
@click.argument("args", nargs=-1)
@click.option("--concept", "concept_id", default=None, help="Focus on a single concept")
@click.option("--top-k", "top_k", type=int, default=20, help="Number of results")
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
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_fragility(obj: dict, args: tuple[str, ...], concept_id: str | None,
                    top_k: int, skip_atms: bool,
                    skip_discovery: bool, skip_conflict: bool,
                    skip_grounding: bool, skip_bridge: bool,
                    ranking_policy: str, fmt: str) -> None:
    """Rank intervention targets by fragility — what to inspect next."""
    from propstore.fragility import FragilityRequest, query_fragility

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, context_id = parse_world_binding_args(args)
        report = query_fragility(
            wm,
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
        result_dict = {
            "world_fragility": report.world_fragility,
            "analysis_scope": report.analysis_scope,
            "interventions": [
                {
                    "intervention_id": item.target.intervention_id,
                    "kind": item.target.kind,
                    "family": item.target.family,
                    "subject_id": item.target.subject_id,
                    "description": item.target.description,
                    "cost_tier": item.target.cost_tier,
                    "local_fragility": item.local_fragility,
                    "roi": item.roi,
                    "ranking_policy": item.ranking_policy,
                    "score_explanation": item.score_explanation,
                }
                for item in report.interventions
            ],
            "interactions": [asdict(i) for i in report.interactions],
        }
        click.echo(json.dumps(result_dict, indent=2))
    else:
        click.echo(f"Fragility Analysis (top {top_k}, ranking={ranking_policy})")
        click.echo("=" * 60)
        click.echo("")
        click.echo(
            f"{'Rank':>4}  {'Score':>5}  {'ROI':>5}  {'Cost':>4}  {'Family':<10} {'Kind':<20} {'Intervention'}"
        )
        for i, item in enumerate(report.interventions, 1):
            roi = f"{item.roi:.2f}"
            cost = str(item.target.cost_tier)
            click.echo(
                f"{i:>4}  {item.local_fragility:>5.2f}  {roi:>5}  {cost:>4}  "
                f"{item.target.family:<10} {item.target.kind:<20} {item.target.intervention_id}"
            )
        click.echo("")
        click.echo(f"World fragility: {report.world_fragility:.2f}")

        # Display interactions if present
        if report.interactions:
            click.echo("")
            click.echo("Interactions:")
            for inter in report.interactions:
                itype = inter.interaction_type
                a_id = inter.intervention_a_id
                b_id = inter.intervention_b_id
                concepts = inter.subjects_affected
                if itype == "synergistic":
                    desc = "synergistic (neither alone flips, both together flip)"
                elif itype == "redundant":
                    desc = "redundant (both alone flip — learning one suffices)"
                elif itype == "mixed":
                    desc = "mixed (synergistic and redundant for different concepts)"
                elif itype == "independent":
                    desc = "independent"
                else:
                    desc = "unknown (no ATMS data)"
                concept_str = f" for {', '.join(concepts)}" if concepts else ""
                click.echo(f"  {a_id} + {b_id}: {desc}{concept_str}")


@world.command("check-consistency")
@click.argument("args", nargs=-1)
@click.option("--transitive", is_flag=True, help="Check multi-hop transitive conflicts")
@click.pass_obj
def world_check_consistency(obj: dict, args: tuple[str, ...],
                            transitive: bool) -> None:
    """Check for conflicts, optionally including transitive (multi-hop) ones.

    Usage: pks world check-consistency domain=example
           pks world check-consistency --transitive
    """
    from propstore.world.consistency import (
        WorldConsistencyRequest,
        check_world_consistency,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = check_world_consistency(
            repo,
            wm,
            WorldConsistencyRequest(bindings=bindings, transitive=transitive),
        )

    if report.transitive:
        if not report.conflicts:
            click.echo("No transitive conflicts found.")
        else:
            click.echo(f"Found {len(report.conflicts)} transitive conflict(s):")
            for conflict in report.conflicts:
                click.echo(
                    f"  {conflict.concept_id}: "
                    f"{conflict.value_a} vs {conflict.value_b}"
                )
                if conflict.derivation_chain:
                    click.echo(f"    chain: {conflict.derivation_chain}")
        return

    if not report.conflicts:
        click.echo("No conflicts under current bindings.")
    else:
        click.echo(f"Found {len(report.conflicts)} conflict(s):")
        for conflict in report.conflicts:
            click.echo(
                f"  {conflict.concept_id}: {conflict.warning_class} "
                f"({conflict.claim_a_id} vs {conflict.claim_b_id})"
            )

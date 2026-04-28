"""Reasoning-oriented ``pks world`` command adapters."""
from __future__ import annotations

import click

from propstore.cli.helpers import EXIT_VALIDATION, fail
from propstore.cli.output import emit, emit_table

from propstore.app.world_reasoning import (
    AppWorldExtensionsRequest,
    WorldExtensionsClaimLine,
    WorldExtensionsUnsupportedBackend,
    world_extensions as run_world_extensions,
)
from propstore.app.rendering import AppRenderPolicyRequest
from propstore.app.world import (
    AppWorldDeriveRequest,
    AppWorldResolveRequest,
    WorldResolveError,
    world_derive as run_world_derive,
    world_resolve as run_world_resolve,
)
from propstore.cli.world import (
    parse_world_binding_args,
    world,
)
from propstore.repository import Repository


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' during derivation.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' during derivation."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to surface if derivation renders them.",
)
@click.pass_obj
def world_derive(
    obj: dict,
    concept_id: str,
    args: tuple[str, ...],
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Derive a value for a concept via parameterization relationships
    under the selected lifecycle-visibility policy.

    Per axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    derivation works over the policy-filtered claim set; opt-in flags
    lift the default hides for drafts / blocked / quarantined rows.

    Usage: pks world derive concept5 domain=example --include-drafts
    """
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = run_world_derive(
        repo,
        AppWorldDeriveRequest(
            concept_id=concept_id,
            bindings=bindings,
            render_policy=AppRenderPolicyRequest(
                include_drafts=include_drafts,
                include_blocked=include_blocked,
                show_quarantined=show_quarantined,
            ),
        ),
    )

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
@click.option("--strategy", required=True,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--override", "override_id", default=None, help="Claim ID for override strategy")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--decision-criterion", "decision_criterion", default="pignistic",
              type=click.Choice([
                  "pignistic",
                  "projected_probability",
                  "lower_bound",
                  "upper_bound",
                  "hurwicz",
              ]),
              help="Decision criterion for opinion interpretation (default: pignistic)")
@click.option("--pessimism-index", "pessimism_index", default=0.5,
              type=float, help="Hurwicz pessimism index α ∈ [0,1] (default: 0.5)")
@click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
              type=click.Choice(["claim_graph", "aspic", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' in resolution input.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' in resolution input."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to inform resolution output.",
)
@click.pass_obj
def world_resolve(obj: dict, concept_id: str, args: tuple[str, ...],
                  strategy: str, override_id: str | None,
                  semantics: str, set_comparison: str,
                  decision_criterion: str,
                  pessimism_index: float,
                  reasoning_backend: str,
                  praf_strategy: str,
                  praf_epsilon: float,
                  praf_confidence: float,
                  praf_seed: int | None,
                  include_drafts: bool,
                  include_blocked: bool,
                  show_quarantined: bool) -> None:
    """Resolve a conflicted concept using a strategy.

    Lifecycle-visibility flags (``--include-drafts``,
    ``--include-blocked``, ``--show-quarantined``) augment the
    constructed ``RenderPolicy`` to surface draft / blocked / quarantined
    rows alongside resolution. Closes axis-1 findings 3.1 / 3.2 / 3.3 per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``.

    Usage: pks world resolve concept1 domain=example --strategy argumentation
    """
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    try:
        report = run_world_resolve(
            repo,
            AppWorldResolveRequest(
                concept_id=concept_id,
                bindings=bindings,
                strategy=strategy,
                override_id=override_id,
                render_policy=AppRenderPolicyRequest(
                    semantics=semantics,
                    set_comparison=set_comparison,
                    decision_criterion=decision_criterion,
                    pessimism_index=pessimism_index,
                    reasoning_backend=reasoning_backend,
                    praf_strategy=praf_strategy,
                    praf_epsilon=praf_epsilon,
                    praf_confidence=praf_confidence,
                    praf_seed=praf_seed,
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldResolveError as exc:
        fail(exc)

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
                (probability.claim_id, f"{probability.probability:.4f}")
                for probability in report.acceptance_probs
            ],
            indent="    ",
        )


@world.command("extensions")
@click.argument("args", nargs=-1)
@click.option("--backend", "backend_name", default="claim_graph",
              type=click.Choice(["claim_graph", "aspic", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--context", default=None, help="Context to scope the argumentation")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.pass_obj
def world_extensions(obj: dict, args: tuple[str, ...],
                     backend_name: str, semantics: str, set_comparison: str,
                     context: str | None,
                     praf_strategy: str,
                     praf_epsilon: float,
                     praf_confidence: float,
                     praf_seed: int | None) -> None:
    """Show argumentation extensions — all claims that survive scrutiny.

    Usage: pks world extensions domain=example --semantics grounded
    """
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    try:
        report = run_world_extensions(
            repo,
            AppWorldExtensionsRequest(
                bindings=bindings,
                backend=backend_name,
                semantics=semantics,
                set_comparison=set_comparison,
                context=context,
                praf_strategy=praf_strategy,
                praf_epsilon=praf_epsilon,
                praf_confidence=praf_confidence,
                praf_seed=praf_seed,
            ),
        )
    except WorldExtensionsUnsupportedBackend as exc:
        fail(exc, exit_code=EXIT_VALIDATION)

    if report is None:
        emit("No active claims for given bindings.")
        return

    claim_map = {claim.claim_id: claim for claim in report.active_claims}
    summary = report.stance_summary

    emit(f"Backend: {report.backend}")
    emit(f"Semantics: {report.semantics}")
    if report.backend == "praf":
        emit(f"Strategy used: {report.strategy_used}")
        if report.samples is not None:
            emit(f"MC samples: {report.samples}")
        emit(f"Active claims: {len(report.active_claims)}")
        emit(
            f"Stances: {summary.total_stances} total, "
            f"{summary.included_as_attacks} included as attacks"
        )
        emit("\nAcceptance probabilities:")
        emit_table(
            ("Claim", "P(accepted)"),
            [
                (
                    _claim_label(probability.claim_id, claim_map),
                    f"{probability.probability:.4f}",
                )
                for probability in report.acceptance_probabilities
            ],
        )
        return

    emit(f"Set comparison: {report.set_comparison}")
    emit(f"Active claims: {len(report.active_claims)}")
    emit(
        f"Stances: {summary.total_stances} total, "
        f"{summary.included_as_attacks} included as attacks, "
        f"{summary.vacuous_count} vacuous, "
        f"{summary.excluded_non_attack} non-attack"
    )
    if summary.models:
        emit(f"Models: {', '.join(summary.models)}")

    if semantics == "grounded":
        accepted = set(report.accepted_claim_ids)
        accepted_groups = _group_by_type(accepted, claim_map)
        emit(f"Accepted ({len(accepted)} claims):")
        for claim_type, claim_ids in sorted(accepted_groups.items()):
            emit(f"  {claim_type} ({len(claim_ids)}):")
            for claim_id in claim_ids:
                emit(f"    {_claim_label(claim_id, claim_map)}")

        if report.defeated_claims:
            emit(f"Defeated ({len(report.defeated_claims)} claims):")
            for defeated in report.defeated_claims:
                emit(f"  {_claim_label(defeated.claim_id, claim_map)}")
                if defeated.defeater_claim_ids:
                    by = ", ".join(defeated.defeater_claim_ids)
                    emit(f"    defeated by: {by}")
        return

    emit(f"Extensions ({len(report.extensions)}):")
    for index, extension in enumerate(report.extensions):
        claim_ids = set(extension.claim_ids)
        emit(f"  Extension {index + 1} ({len(claim_ids)} claims):")
        groups = _group_by_type(claim_ids, claim_map)
        for claim_type, grouped_claim_ids in sorted(groups.items()):
            emit(f"    {claim_type}:")
            for claim_id in grouped_claim_ids:
                emit(f"      {_claim_label(claim_id, claim_map)}")


def _claim_label(
    claim_id: str,
    claim_map: dict[str, WorldExtensionsClaimLine],
) -> str:
    claim = claim_map.get(claim_id)
    if claim is None:
        return claim_id

    claim_type = claim.claim_type or "unknown"
    if claim_type == "parameter" and claim.value is not None:
        return f"{claim_id}: {claim.concept_name} = {claim.value}"
    if claim_type == "equation":
        expr = claim.expression or ""
        return f"{claim_id}: {expr}" if expr else f"{claim_id} ({claim_type})"
    if claim_type in ("observation", "limitation", "mechanism", "comparison"):
        stmt = claim.statement or claim.description or ""
        if len(stmt) > 60:
            stmt = stmt[:57] + "..."
        return f"{claim_id}: {stmt}" if stmt else f"{claim_id} ({claim_type})"
    if claim.value is not None:
        if claim.concept_name:
            return f"{claim_id}: {claim.concept_name} = {claim.value}"
        return f"{claim_id} = {claim.value}"
    return f"{claim_id} ({claim_type})"


def _group_by_type(
    claim_ids: set[str],
    claim_map: dict[str, WorldExtensionsClaimLine],
) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for claim_id in sorted(claim_ids):
        claim = claim_map.get(claim_id)
        claim_type = claim.claim_type if claim is not None else "unknown"
        groups.setdefault(claim_type or "unknown", []).append(claim_id)
    return groups

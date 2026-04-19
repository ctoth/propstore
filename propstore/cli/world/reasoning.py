"""Reasoning-oriented ``pks world`` command adapters."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, cast
import sys

import click

from propstore.app.world import (
    AppWorldDeriveRequest,
    AppWorldResolveRequest,
    WorldLifecycleOptions,
    bind_world,
    open_app_world_model,
    parse_world_binding_args,
    resolve_world_target,
    world_derive as run_world_derive,
    world_resolve as run_world_resolve,
)
from propstore.cli.world import (
    world,
)
from propstore.repository import Repository
from propstore.world.queries import WorldResolveError

if TYPE_CHECKING:
    from propstore.core.active_claims import ActiveClaim
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.core.labels import Label, SupportQuality


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
            lifecycle=WorldLifecycleOptions(
                include_drafts=include_drafts,
                include_blocked=include_blocked,
                show_quarantined=show_quarantined,
            ),
        ),
    )

    click.echo(f"{report.concept_id}: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    if report.formula:
        click.echo(f"  formula: {report.formula}")
    if report.input_values:
        click.echo(f"  inputs: {report.input_values}")
    if report.exactness:
        click.echo(f"  exactness: {report.exactness}")


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
              type=click.Choice(["pignistic", "lower_bound", "upper_bound", "hurwicz"]),
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
                semantics=semantics,
                set_comparison=set_comparison,
                decision_criterion=decision_criterion,
                pessimism_index=pessimism_index,
                reasoning_backend=reasoning_backend,
                praf_strategy=praf_strategy,
                praf_epsilon=praf_epsilon,
                praf_confidence=praf_confidence,
                praf_seed=praf_seed,
                lifecycle=WorldLifecycleOptions(
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldResolveError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

    click.echo(f"{report.concept_display_id}: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    if report.winning_claim_display_id:
        click.echo(f"  winner: {report.winning_claim_display_id}")
    if report.strategy:
        click.echo(f"  strategy: {report.strategy}")
    if report.reason:
        click.echo(f"  reason: {report.reason}")
    if report.acceptance_probs:
        click.echo("  acceptance_probs:")
        for probability in report.acceptance_probs:
            click.echo(f"    {probability.claim_id}: {probability.probability:.4f}")


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
    from propstore.relation_analysis import stance_summary
    from propstore.world import ReasoningBackend
    from propstore.world.types import normalize_reasoning_backend

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        from propstore.core.active_claims import coerce_active_claims

        bindings, _ = parse_world_binding_args(args)
        bound = bind_world(wm, bindings, context_id=context)
        active = coerce_active_claims(bound.active_claims())
        if not active:
            click.echo("No active claims for given bindings.")
            return

        claim_ids = {str(claim.claim_id) for claim in active}
        backend = normalize_reasoning_backend(backend_name)

        if backend == ReasoningBackend.ATMS:
            click.echo(
                "ERROR: backend 'atms' does not expose Dung extensions; "
                "use worldline or resolve with reasoning_backend=atms instead.",
                err=True,
            )
            sys.exit(2)

        if backend == ReasoningBackend.PRAF:
            from argumentation.probabilistic import compute_probabilistic_acceptance
            from propstore.praf import build_praf

            praf = build_praf(wm, claim_ids, comparison=set_comparison)
            praf_result = compute_probabilistic_acceptance(
                praf.kernel, semantics=semantics,
                strategy=praf_strategy,
                query_kind="argument_acceptance",
                inference_mode="credulous",
                mc_epsilon=praf_epsilon,
                mc_confidence=praf_confidence,
                rng_seed=praf_seed,
            )
            summary = stance_summary(wm, claim_ids)
            click.echo(f"Backend: {backend.value}")
            click.echo(f"Semantics: {semantics}")
            click.echo(f"Strategy used: {praf_result.strategy_used}")
            if praf_result.samples is not None:
                click.echo(f"MC samples: {praf_result.samples}")
            click.echo(f"Active claims: {len(claim_ids)}")
            click.echo(f"Stances: {summary['total_stances']} total, "
                       f"{summary['included_as_attacks']} included as attacks")
            click.echo("\nAcceptance probabilities:")
            claim_map = {str(claim.claim_id): claim for claim in active}
            acceptance_probs = (
                {}
                if praf_result.acceptance_probs is None
                else praf_result.acceptance_probs
            )
            for cid, prob in sorted(
                acceptance_probs.items(),
                key=lambda x: -x[1],
            ):
                c = claim_map.get(cid)
                label = cid
                if c:
                    value = c.value
                    concept_id_val = None if c.concept_id is None else str(c.concept_id)
                    if concept_id_val:
                        concept = wm.get_concept(concept_id_val)
                        if concept is None:
                            cname = concept_id_val
                        else:
                            from propstore.core.row_types import coerce_concept_row

                            cname = coerce_concept_row(concept).canonical_name
                        if value is not None:
                            label = f"{cid}: {cname} = {value}"
                        else:
                            label = f"{cid}: {cname}"
                click.echo(f"  {label}  P(accepted) = {prob:.4f}")
            return

        if backend == ReasoningBackend.CLAIM_GRAPH:
            from propstore.claim_graph import (
                build_argumentation_framework,
                compute_claim_graph_justified_claims,
            )

            result = compute_claim_graph_justified_claims(
                wm, claim_ids,
                semantics=semantics,
                comparison=set_comparison,
            )
            af = build_argumentation_framework(
                wm, claim_ids,
                comparison=set_comparison,
            )
            arg_to_claim = {cid: cid for cid in claim_ids}
        elif backend == ReasoningBackend.ASPIC:
            from propstore.structured_projection import (
                build_structured_projection,
                compute_structured_justified_arguments,
            )
            from propstore.grounding.bundle import GroundedRulesBundle

            grounding_bundle = GroundedRulesBundle.empty()
            bundle_getter = getattr(wm, "grounding_bundle", None)
            if callable(bundle_getter):
                typed_bundle_getter = cast(
                    Callable[[], GroundedRulesBundle],
                    bundle_getter,
                )
                grounding_bundle = typed_bundle_getter()

            aspic_projection = build_structured_projection(
                wm,
                active,
                bundle=grounding_bundle,
                support_metadata=_support_metadata_for(bound, active),
                comparison=set_comparison,
                active_graph=_active_graph_for(bound),
            )
            result = compute_structured_justified_arguments(
                aspic_projection,
                semantics=semantics,
                backend=ReasoningBackend.ASPIC,
            )
            af = aspic_projection.framework
            arg_to_claim = dict(aspic_projection.argument_to_claim_id)
        else:
            raise NotImplementedError(f"Unknown backend: {backend.value}")

        summary = stance_summary(wm, claim_ids)
        click.echo(f"Backend: {backend.value}")
        click.echo(f"Semantics: {semantics}")
        click.echo(f"Set comparison: {set_comparison}")
        click.echo(f"Active claims: {len(claim_ids)}")
        click.echo(f"Stances: {summary['total_stances']} total, "
                   f"{summary['included_as_attacks']} included as attacks, "
                   f"{summary['vacuous_count']} vacuous, "
                   f"{summary['excluded_non_attack']} non-attack")
        if summary["models"]:
            click.echo(f"Models: {', '.join(summary['models'])}")

        claim_map = {str(claim.claim_id): claim for claim in active}

        def _claim_label(cid: str) -> str:
            """Format a claim for display: id (type) concept = value."""
            c = claim_map.get(cid)
            if c is None:
                return cid
            ctype = c.claim_type or "?"
            concept_id = None if c.concept_id is None else str(c.concept_id)
            value = c.value
            cname = None
            if concept_id:
                concept = wm.get_concept(concept_id)
                if concept:
                    from propstore.core.row_types import coerce_concept_row

                    cname = coerce_concept_row(concept).canonical_name
            if ctype == "parameter" and value is not None:
                return f"{cid}: {cname} = {value}"
            if ctype == "equation":
                expr = c.expression or ""
                return f"{cid}: {expr}" if expr else f"{cid} ({ctype})"
            if ctype in ("observation", "limitation", "mechanism", "comparison"):
                stmt = c.statement or c.description or ""
                if len(stmt) > 60:
                    stmt = stmt[:57] + "..."
                return f"{cid}: {stmt}" if stmt else f"{cid} ({ctype})"
            if value is not None:
                return f"{cid}: {cname} = {value}" if cname else f"{cid} = {value}"
            return f"{cid} ({ctype})"

        def _group_by_type(cids: set[str]) -> dict[str, list[str]]:
            groups: dict[str, list[str]] = {}
            for cid in sorted(cids):
                c = claim_map.get(cid)
                ctype = c.claim_type if c and c.claim_type else "unknown"
                groups.setdefault(ctype, []).append(cid)
            return groups

        if semantics == "grounded":
            if backend == ReasoningBackend.ASPIC:
                assert isinstance(result, frozenset)
                justified_claims = {
                    claim_id
                    for arg_id in result
                    if (claim_id := arg_to_claim.get(arg_id)) is not None
                }
            else:
                assert isinstance(result, frozenset)
                justified_claims = set(result)

            defeated = claim_ids - justified_claims
            defeaters_map: dict[str, list[str]] = {}
            for src, tgt in af.defeats:
                src_claim = arg_to_claim.get(src, src)
                tgt_claim = arg_to_claim.get(tgt, tgt)
                if tgt_claim in defeated:
                    defeaters_map.setdefault(tgt_claim, []).append(src_claim)

            accepted_groups = _group_by_type(justified_claims)
            click.echo(f"Accepted ({len(justified_claims)} claims):")
            for ctype, cids in sorted(accepted_groups.items()):
                click.echo(f"  {ctype} ({len(cids)}):")
                for cid in cids:
                    click.echo(f"    {_claim_label(cid)}")

            if defeated:
                click.echo(f"Defeated ({len(defeated)} claims):")
                for cid in sorted(defeated):
                    defeaters = defeaters_map.get(cid, [])
                    if defeaters:
                        by = ", ".join(sorted(defeaters))
                        click.echo(f"  {_claim_label(cid)}")
                        click.echo(f"    defeated by: {by}")
                    else:
                        click.echo(f"  {_claim_label(cid)}")
        else:
            assert isinstance(result, list)
            click.echo(f"Extensions ({len(result)}):")
            for i, ext in enumerate(result):
                ext_claims = (
                    {
                        claim_id
                        for arg_id in ext
                        if (claim_id := arg_to_claim.get(arg_id)) is not None
                    }
                    if backend == ReasoningBackend.ASPIC
                    else set(ext)
                )
                click.echo(f"  Extension {i + 1} ({len(ext_claims)} claims):")
                groups = _group_by_type(ext_claims)
                for ctype, cids in sorted(groups.items()):
                    click.echo(f"    {ctype}:")
                    for cid in cids:
                        click.echo(f"      {_claim_label(cid)}")


def _support_metadata_for(
    bound: object,
    active_claims: Sequence["ActiveClaim"],
) -> dict[str, tuple[Label | None, SupportQuality]]:
    from propstore.world.types import ClaimSupportView

    if not isinstance(bound, ClaimSupportView):
        return {}

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    for claim in active_claims:
        support_metadata[str(claim.claim_id)] = bound.claim_support(claim)
    return support_metadata


def _active_graph_for(bound: object) -> ActiveWorldGraph | None:
    from propstore.world.types import HasActiveGraph

    if isinstance(bound, HasActiveGraph):
        return bound._active_graph
    return None

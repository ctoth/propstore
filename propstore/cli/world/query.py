"""Basic ``pks world`` query command adapters."""
from __future__ import annotations

import sys

import click

from propstore.cli.helpers import open_world_model
from propstore.cli.world import (
    _bind_world,
    _lifecycle_policy,
    _parse_bindings,
    _resolve_world_target,
    world,
)
from propstore.repository import Repository


@world.command("status")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' in the counts.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' in the counts."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help=(
        "Surface a Diagnostics count line sourced from build_diagnostics."
    ),
)
@click.pass_obj
def world_status(
    obj: dict,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Show knowledge base stats (concepts, claims, conflicts).

    Claim counts reflect the lifecycle-visibility policy selected by the
    three opt-in flags. Closes axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    the sidecar holds every row and the render layer decides what to
    report.
    """
    from propstore.world.queries import WorldStatusRequest, get_world_status

    repo: Repository = obj["repo"]
    policy = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)
    with open_world_model(repo) as wm:
        report = get_world_status(wm, WorldStatusRequest(policy=policy))
        click.echo(f"Concepts: {report.concept_count}")
        click.echo(f"Claims:   {report.visible_claim_count}")
        click.echo(f"Conflicts: {report.conflict_count}")
        if policy.show_quarantined:
            click.echo(f"Diagnostics: {report.diagnostic_count}")


@world.command("query")
@click.argument("concept_id")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft'.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked'."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help=(
        "Append a Diagnostics block sourced from build_diagnostics."
    ),
)
@click.pass_obj
def world_query(
    obj: dict,
    concept_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Show all claims for a concept under the lifecycle-visibility
    policy.

    Closes axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    the default output excludes rows quarantined by the build
    (``build_status='blocked'``), drafts (``stage='draft'``), and
    promotion-blocked mirror rows; opt-in flags lift each filter.
    """
    from propstore.world.queries import (
        UnknownConceptError,
        WorldConceptQueryRequest,
        query_world_concept,
    )

    repo: Repository = obj["repo"]
    policy = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)
    with open_world_model(repo) as wm:
        try:
            report = query_world_concept(
                wm,
                WorldConceptQueryRequest(target=concept_id, policy=policy),
            )
        except UnknownConceptError:
            click.echo(f"Unknown concept: {concept_id}", err=True)
            sys.exit(1)

        click.echo(f"{report.canonical_name} ({report.concept_display_id})")
        if not report.claims:
            click.echo("  (no claims)")
        for claim in report.claims:
            click.echo(
                f"  {claim.display_id}: {claim.claim_type} "
                f"{claim.value_display} conditions={claim.conditions}"
            )
        if policy.show_quarantined:
            if report.diagnostics:
                click.echo("Diagnostics:")
                for diagnostic in report.diagnostics:
                    click.echo(
                        f"  {diagnostic.target} "
                        f"[{diagnostic.diagnostic_kind}] {diagnostic.message}"
                    )


@world.command("bind")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_bind(obj: dict, args: tuple[str, ...]) -> None:
    """Show active claims under condition bindings.

    Usage: pks world bind domain=example [concept_id]

    Arguments with '=' are bindings, the last argument without '=' is a concept filter.
    """
    from propstore.world.queries import (
        WorldBindActiveReport,
        WorldBindConceptReport,
        WorldBindRequest,
        query_bound_world,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, query_concept = _parse_bindings(args)
        report = query_bound_world(
            wm,
            WorldBindRequest(bindings=bindings, target=query_concept),
        )

        if isinstance(report, WorldBindConceptReport):
            click.echo(f"{report.concept_display_id}: {report.status}")
            for claim in report.claims:
                click.echo(
                    f"  {claim.display_id}: {claim.value_display} "
                    f"source={claim.source}"
                )
            return

        assert isinstance(report, WorldBindActiveReport)
        click.echo(f"Active claims: {report.active_claim_count}")
        for claim in report.claims:
            click.echo(
                f"  {claim.display_id}: {claim.concept_display_id} "
                f"{claim.value_display} conditions={claim.conditions}"
            )


@world.command("explain")
@click.argument("claim_id")
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    from propstore.world.queries import (
        UnknownClaimError,
        WorldExplainRequest,
        explain_world_claim,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        try:
            report = explain_world_claim(wm, WorldExplainRequest(claim_id=claim_id))
        except UnknownClaimError:
            click.echo(f"Unknown claim: {claim_id}", err=True)
            sys.exit(1)

    click.echo(
        f"{report.claim_display_id}: {report.claim_type} "
        f"concept={report.concept_display_id} "
        f"value={report.value}"
    )
    if not report.stances:
        click.echo("  (no stances)")
    for stance in report.stances:
        indent = "    " if stance.nested else "  "
        click.echo(
            f"{indent}{stance.source_display_id} "
            f"{stance.stance_type} -> {stance.target_display_id}"
            f" (strength={stance.strength}, note={stance.note})"
        )


@world.command("algorithms")
@click.option("--stage", default=None, help="Filter by processing stage")
@click.option("--concept", default=None, help="Filter by concept")
@click.pass_obj
def world_algorithms(obj: dict, stage: str | None, concept: str | None) -> None:
    """List algorithm claims in the world model."""
    from propstore.world.queries import (
        WorldAlgorithmsRequest,
        list_world_algorithms,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        report = list_world_algorithms(
            wm,
            WorldAlgorithmsRequest(stage=stage, concept=concept),
        )

    if not report.algorithms:
        click.echo("No algorithm claims found.")
        return

    # Table header
    click.echo(f"{'ID':<20} {'Name':<30} {'Stage':<15} {'Concept(s)'}")
    click.echo("-" * 80)
    for claim in report.algorithms:
        click.echo(
            f"{claim.claim_id:<20} {claim.name:<30} "
            f"{claim.stage:<15} {claim.concept_id}"
        )

    click.echo(f"\n{len(report.algorithms)} algorithm claim(s).")

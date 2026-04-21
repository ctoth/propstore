"""Basic ``pks world`` query command adapters."""
from __future__ import annotations

import click

from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_table

from propstore.app.world import (
    AppWorldAlgorithmsRequest,
    AppWorldBindRequest,
    AppWorldConceptQueryRequest,
    AppWorldExplainRequest,
    AppWorldStatusRequest,
    UnknownClaimError,
    UnknownConceptError,
    WorldBindActiveReport,
    WorldBindConceptReport,
    WorldLifecycleOptions,
    world_algorithms as run_world_algorithms,
    world_bind as run_world_bind,
    world_concept_query,
    world_explain as run_world_explain,
    world_status as run_world_status,
)
from propstore.cli.world import (
    parse_world_binding_args,
    world,
)
from propstore.repository import Repository


def _lifecycle_options(
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> WorldLifecycleOptions:
    return WorldLifecycleOptions(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )


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
    repo: Repository = obj["repo"]
    lifecycle = _lifecycle_options(include_drafts, include_blocked, show_quarantined)
    report = run_world_status(repo, AppWorldStatusRequest(lifecycle=lifecycle))
    emit(f"Concepts: {report.concept_count}")
    emit(f"Claims:   {report.visible_claim_count}")
    emit(f"Conflicts: {report.conflict_count}")
    if lifecycle.show_quarantined:
        emit(f"Diagnostics: {report.diagnostic_count}")


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
    repo: Repository = obj["repo"]
    lifecycle = _lifecycle_options(include_drafts, include_blocked, show_quarantined)
    try:
        report = world_concept_query(
            repo,
            AppWorldConceptQueryRequest(target=concept_id, lifecycle=lifecycle),
        )
    except UnknownConceptError:
        fail(f"Unknown concept: {concept_id}")

    emit(f"{report.canonical_name} ({report.concept_display_id})")
    if not report.claims:
        emit("  (no claims)")
    for claim in report.claims:
        emit(
            f"  {claim.display_id}: {claim.claim_type} "
            f"{claim.value_display} conditions={claim.conditions}"
        )
    if lifecycle.show_quarantined and report.diagnostics:
        emit("Diagnostics:")
        for diagnostic in report.diagnostics:
            emit(
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
    repo: Repository = obj["repo"]
    bindings, query_concept = parse_world_binding_args(args)
    report = run_world_bind(
        repo,
        AppWorldBindRequest(bindings=bindings, target=query_concept),
    )

    if isinstance(report, WorldBindConceptReport):
        emit(f"{report.concept_display_id}: {report.status}")
        for claim in report.claims:
            emit(
                f"  {claim.display_id}: {claim.value_display} "
                f"source={claim.source}"
            )
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
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    repo: Repository = obj["repo"]
    try:
        report = run_world_explain(repo, AppWorldExplainRequest(claim_id=claim_id))
    except UnknownClaimError:
        fail(f"Unknown claim: {claim_id}")

    emit(
        f"{report.claim_display_id}: {report.claim_type} "
        f"concept={report.concept_display_id} "
        f"value={report.value}"
    )
    if not report.stances:
        emit("  (no stances)")
    for stance in report.stances:
        indent = "    " if stance.nested else "  "
        emit(
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
    repo: Repository = obj["repo"]
    report = run_world_algorithms(
        repo,
        AppWorldAlgorithmsRequest(stage=stage, concept=concept),
    )

    if not report.algorithms:
        emit("No algorithm claims found.")
        return

    emit_table(
        ("ID", "Name", "Stage", "Concept(s)"),
        [
            (claim.claim_id, claim.name, claim.stage, claim.concept_id)
            for claim in report.algorithms
        ],
    )

    emit(f"\n{len(report.algorithms)} algorithm claim(s).")

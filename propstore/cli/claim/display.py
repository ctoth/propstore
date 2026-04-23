from __future__ import annotations

import click

from propstore.app.claim_views import (
    ClaimListRequest,
    ClaimSearchRequest,
    ClaimViewReport,
    ClaimViewRequest,
    ClaimViewUnknownClaimError,
    build_claim_view,
    list_claim_views,
    search_claim_views,
)
from propstore.app.neighborhoods import (
    SemanticNeighborhoodRequest,
    build_semantic_neighborhood,
)
from propstore.app.world import WorldSidecarMissingError
from propstore.cli.claim import claim, claim_render_policy_options, claim_render_policy_request
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_section, emit_table
from propstore.repository import Repository


def _render_claim_view(report: ClaimViewReport) -> None:
    if report.logical_id:
        emit(f"Logical ID: {report.logical_id}")
    emit(f"Artifact ID: {report.artifact_id}")
    if report.version_id:
        emit(f"Version ID: {report.version_id}")

    emit(f"  status: {report.status.state}")
    emit(
        "  visible_under_policy: "
        + ("yes" if report.status.visible_under_policy else "no")
    )
    if not report.status.visible_under_policy:
        emit(f"  policy: {report.status.reason}")
    emit(
        "  lifecycle: "
        f"branch={report.status.branch} "
        f"build={report.status.build_status} "
        f"stage={report.status.stage} "
        f"promotion={report.status.promotion_status}"
    )

    if report.concept.concept_id:
        emit(f"  concept: {report.concept.concept_id}")
    if report.concept.canonical_name:
        emit(f"  concept_name: {report.concept.canonical_name}")
    if report.claim_type:
        emit(f"  type: {report.claim_type}")
    if report.statement:
        emit(f"  statement: {report.statement}")

    if report.value.value is not None:
        emit(f"  value: {report.value.value} {report.value.unit or ''}".rstrip())
        if (
            report.value.value_si is not None
            and report.value.value_si != report.value.value
        ):
            si_label = (
                f"{report.value.value_si} {report.value.canonical_unit or ''}"
            ).rstrip()
            emit(f"  value (SI): {si_label}")
    elif report.value.state != "missing":
        emit(f"  value: {report.value.sentence}")

    if report.uncertainty.lower_bound is not None:
        si_part = (
            f" -> {report.uncertainty.lower_bound_si}"
            if report.uncertainty.lower_bound_si is not None
            and report.uncertainty.lower_bound_si != report.uncertainty.lower_bound
            else ""
        )
        emit(f"  lower_bound: {report.uncertainty.lower_bound}{si_part}")
    if report.uncertainty.upper_bound is not None:
        si_part = (
            f" -> {report.uncertainty.upper_bound_si}"
            if report.uncertainty.upper_bound_si is not None
            and report.uncertainty.upper_bound_si != report.uncertainty.upper_bound
            else ""
        )
        emit(f"  upper_bound: {report.uncertainty.upper_bound}{si_part}")
    if report.uncertainty.uncertainty is not None:
        emit(f"  uncertainty: {report.uncertainty.uncertainty}")
    if report.uncertainty.sample_size is not None:
        emit(f"  sample_size: {report.uncertainty.sample_size}")

    provenance_label = (
        report.provenance.paper
        or report.provenance.source_id
        or report.provenance.source_slug
    )
    if provenance_label:
        emit(f"  source: {provenance_label}")
    if report.provenance.page is not None:
        emit(f"  page: {report.provenance.page}")
    if report.condition.expression:
        emit(f"  conditions: {report.condition.expression}")


@claim.command("show")
@click.argument("claim_id")
@claim_render_policy_options
@click.pass_obj
def show(
    obj: dict,
    claim_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Display details of a single claim."""
    repo: Repository = obj["repo"]
    try:
        report = build_claim_view(
            repo,
            ClaimViewRequest(
                claim_id=claim_id,
                render_policy=claim_render_policy_request(
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldSidecarMissingError as exc:
        fail(exc)
    except ClaimViewUnknownClaimError:
        fail(f"Claim '{claim_id}' not found.")
    _render_claim_view(report)


@claim.command("list")
@click.option("--concept", default=None, help="Filter by concept id or canonical name.")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows to show.")
@claim_render_policy_options
@click.pass_obj
def list_cmd(
    obj: dict,
    concept: str | None,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """List claims visible under the current render policy."""
    repo: Repository = obj["repo"]
    try:
        report = list_claim_views(
            repo,
            ClaimListRequest(
                concept=concept,
                limit=limit,
                render_policy=claim_render_policy_request(
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldSidecarMissingError as exc:
        fail(exc)
    if not report.entries:
        emit("No claims found.")
        return
    emit_table(
        ("ID", "Concept", "Type", "Value"),
        [
            (
                entry.logical_id or entry.claim_id,
                entry.concept_name or entry.concept_id or "-",
                entry.claim_type,
                entry.value_display,
            )
            for entry in report.entries
        ],
    )


@claim.command("search")
@click.argument("query")
@click.option("--concept", default=None, help="Filter by concept id or canonical name.")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows to show.")
@claim_render_policy_options
@click.pass_obj
def search(
    obj: dict,
    query: str,
    concept: str | None,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Search claims visible under the current render policy."""
    repo: Repository = obj["repo"]
    try:
        report = search_claim_views(
            repo,
            ClaimSearchRequest(
                query=query,
                concept=concept,
                limit=limit,
                render_policy=claim_render_policy_request(
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldSidecarMissingError as exc:
        fail(exc)
    if not report.entries:
        emit("No matches.")
        return
    emit_table(
        ("ID", "Concept", "Type", "Value"),
        [
            (
                entry.logical_id or entry.claim_id,
                entry.concept_name or entry.concept_id or "-",
                entry.claim_type,
                entry.value_display,
            )
            for entry in report.entries
        ],
    )


@claim.command("neighborhood")
@click.argument("claim_id")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum neighborhood rows to show.")
@claim_render_policy_options
@click.pass_obj
def neighborhood(
    obj: dict,
    claim_id: str,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Show the semantic neighborhood around a claim."""
    repo: Repository = obj["repo"]
    try:
        report = build_semantic_neighborhood(
            repo,
            SemanticNeighborhoodRequest(
                focus_kind="claim",
                focus_id=claim_id,
                limit=limit,
                render_policy=claim_render_policy_request(
                    include_drafts=include_drafts,
                    include_blocked=include_blocked,
                    show_quarantined=show_quarantined,
                ),
            ),
        )
    except WorldSidecarMissingError as exc:
        fail(exc)
    except ClaimViewUnknownClaimError:
        fail(f"Claim '{claim_id}' not found.")

    emit(f"Focus: {report.focus.display_id}")
    emit(f"Status: {report.status.state}")
    if not report.status.visible_under_policy:
        emit(f"  policy: {report.status.reason}")
    emit(report.prose_summary)
    emit_section("Moves:", (move.sentence for move in report.moves))
    emit_section(
        "Neighborhood:",
        (f"[{row.section}] {row.sentence}" for row in report.table_rows[:limit]),
    )

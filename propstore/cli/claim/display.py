"""``pks claim`` read-view command adapters.

``show`` / ``list`` / ``search`` over the per-field and summary view builders in
:mod:`propstore.app.claim_views` and :mod:`propstore.app.claims`, ``neighborhood``
over :mod:`propstore.app.neighborhoods`, and ``compare`` over
:func:`propstore.app.claims.compare_algorithm_claims`. Each command opens a world
reader, calls the owner builder under a lifecycle render policy, and renders the
typed report; typed owner failures map to clean exit codes via ``fail``.
"""

from __future__ import annotations

import click

from propstore.app.claim_views import (
    ClaimViewBlockedError,
    ClaimViewUnknownClaimError,
    build_claim_view,
)
from propstore.app.claims import (
    ClaimCompareRequest,
    ClaimComparisonError,
    UnknownClaimError,
    compare_algorithm_claims,
    list_claim_views,
    search_claim_views,
)
from propstore.app.neighborhoods import (
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.cli.claim import (
    claim,
    emit_report_json,
    format_option,
    lifecycle_options,
    lifecycle_policy,
    open_world,
)
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table


@claim.command("show")
@click.argument("claim_id")
@lifecycle_options
@format_option
@click.pass_obj
def claim_show(
    obj: CliContext,
    claim_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Show one claim's per-field view under the lifecycle-visibility policy."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        try:
            report = build_claim_view(world_query, claim_id, policy=policy)
        except ClaimViewUnknownClaimError:
            fail(f"Unknown claim: {claim_id}")
        except ClaimViewBlockedError:
            fail(
                f"Claim {claim_id} is blocked under the current render policy "
                "(retry with --include-blocked / --include-drafts)."
            )

    if fmt == "json":
        emit_report_json(report)
        return
    emit(report.heading)
    emit(f"  type:        {report.claim_type}")
    if report.name:
        emit(f"  name:        {report.name}")
    emit(f"  concept:     {report.concept.sentence}")
    emit(f"  value:       {report.value.sentence}")
    emit(f"  uncertainty: {report.uncertainty.sentence}")
    emit(f"  condition:   {report.condition.sentence}")
    emit(f"  provenance:  {report.provenance.sentence}")
    emit(f"  status:      {report.status.reason}")


@claim.command("list")
@click.option("--concept", default=None, help="Filter to claims about this concept.")
@click.option("--limit", default=50, type=click.IntRange(min=1), help="Maximum rows.")
@lifecycle_options
@format_option
@click.pass_obj
def claim_list(
    obj: CliContext,
    concept: str | None,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """List policy-visible claims, optionally scoped to one concept."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        report = list_claim_views(
            world_query, policy=policy, concept=concept, limit=limit
        )

    if fmt == "json":
        emit_report_json(report)
        return
    _emit_summary(report)


@claim.command("search")
@click.argument("query")
@click.option("--concept", default=None, help="Filter to claims about this concept.")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows.")
@lifecycle_options
@format_option
@click.pass_obj
def claim_search(
    obj: CliContext,
    query: str,
    concept: str | None,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Search policy-visible claims by text match."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        report = search_claim_views(
            world_query, query, policy=policy, concept=concept, limit=limit
        )

    if fmt == "json":
        emit_report_json(report)
        return
    _emit_summary(report)


@claim.command("neighborhood")
@click.argument("claim_id")
@click.option(
    "--limit", default=50, type=click.IntRange(min=1), help="Maximum neighbors."
)
@lifecycle_options
@format_option
@click.pass_obj
def claim_neighborhood(
    obj: CliContext,
    claim_id: str,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Show the argumentative neighborhood of a focus claim."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        try:
            report = build_semantic_neighborhood(
                world_query, "claim", claim_id, policy=policy, limit=limit
            )
        except ClaimViewUnknownClaimError:
            fail(f"Unknown claim: {claim_id}")
        except ClaimViewBlockedError:
            fail(
                f"Claim {claim_id} is blocked under the current render policy "
                "(retry with --include-blocked / --include-drafts)."
            )
        except SemanticNeighborhoodUnsupportedFocusError as exc:
            fail(str(exc))

    if fmt == "json":
        emit_report_json(report)
        return
    emit(report.focus.sentence)
    for move in report.moves:
        emit(f"  {move.kind}: {move.sentence}")
    emit(report.prose_summary)


@claim.command("compare")
@click.argument("claim_a")
@click.argument("claim_b")
@click.option(
    "--known",
    "known",
    multiple=True,
    help="A KEY=VALUE numeric binding passed to the partial-eval comparison tier.",
)
@format_option
@click.pass_obj
def claim_compare(
    obj: CliContext,
    claim_a: str,
    claim_b: str,
    known: tuple[str, ...],
    fmt: str,
) -> None:
    """Compare two algorithm claims' bodies for equivalence (AST equivalence)."""

    repo = require_repo(obj)
    known_values = _parse_known_values(known)
    with open_world(repo) as world_query:
        try:
            report = compare_algorithm_claims(
                world_query,
                ClaimCompareRequest(
                    claim_a_id=claim_a,
                    claim_b_id=claim_b,
                    known_values=known_values,
                ),
            )
        except UnknownClaimError as exc:
            fail(str(exc))
        except ClaimComparisonError as exc:
            fail(str(exc))

    if fmt == "json":
        emit_report_json(report)
        return
    verdict = "equivalent" if report.equivalent else "not equivalent"
    emit(f"{claim_a} vs {claim_b}: {verdict} (tier={report.tier})")
    emit(f"  similarity: {report.similarity}")
    emit(f"  details:    {report.details}")


def _parse_known_values(known: tuple[str, ...]) -> dict[str, float] | None:
    if not known:
        return None
    parsed: dict[str, float] = {}
    for item in known:
        key, sep, value = item.partition("=")
        if not sep or not key:
            fail(f"--known expects KEY=VALUE, got {item!r}")
        try:
            parsed[key] = float(value)
        except ValueError:
            fail(f"--known value for {key!r} must be numeric, got {value!r}")
    return parsed


def _emit_summary(report: object) -> None:
    from propstore.app.claims import ClaimSummaryReport

    if not isinstance(report, ClaimSummaryReport):  # pragma: no cover - typing guard
        raise TypeError("expected a ClaimSummaryReport")
    if not report.entries:
        emit("No claims found.")
        return
    emit_table(
        ("ID", "Concept", "Type", "Value", "Condition"),
        [
            (
                entry.claim_id,
                entry.concept_display,
                entry.claim_type,
                entry.value_display,
                entry.condition_display,
            )
            for entry in report.entries
        ],
    )
    emit(f"\n{len(report.entries)} claim(s).")

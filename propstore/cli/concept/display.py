"""``pks concept`` read-view command adapters.

``list`` / ``search`` over :mod:`propstore.app.concepts` and ``show`` over
:func:`propstore.app.concept_views.build_concept_view`. Each command opens a world
reader, calls the owner builder under a lifecycle render policy, and renders the
typed report; typed owner failures map to clean exit codes via ``fail``.
"""

from __future__ import annotations

import click

from propstore.app.concept_views import (
    ConceptViewUnknownConceptError,
    build_concept_view,
)
from propstore.app.concepts.display import (
    ConceptSearchSyntaxError,
    list_concepts,
    search_concepts,
)
from propstore.cli.concept import (
    concept,
    emit_report_json,
    format_option,
    lifecycle_options,
    lifecycle_policy,
    open_world,
)
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_table


@concept.command("list")
@click.option("--limit", default=50, type=click.IntRange(min=1), help="Maximum rows.")
@lifecycle_options
@format_option
@click.pass_obj
def concept_list(
    obj: CliContext,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """List policy-visible concepts."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        report = list_concepts(world_query, policy=policy, limit=limit)

    if fmt == "json":
        emit_report_json(report)
        return
    if not report.concepts_found:
        emit("No concepts found.")
        return
    if not report.entries:
        emit("No concepts visible under the current render policy.")
        return
    emit_table(
        ("ID", "Name", "Status"),
        [
            (entry.concept_id, entry.canonical_name, entry.status)
            for entry in report.entries
        ],
    )
    emit(f"\n{len(report.entries)} concept(s).")


@concept.command("search")
@click.argument("query")
@click.option("--limit", default=20, type=click.IntRange(min=1), help="Maximum rows.")
@lifecycle_options
@format_option
@click.pass_obj
def concept_search(
    obj: CliContext,
    query: str,
    limit: int,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Search policy-visible concepts by name."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        try:
            report = search_concepts(world_query, query, policy=policy, limit=limit)
        except ConceptSearchSyntaxError as exc:
            fail(str(exc))

    if fmt == "json":
        emit_report_json(report)
        return
    if not report.hits:
        emit("No matches.")
        return
    emit_table(
        ("ID", "Name", "Status"),
        [(hit.concept_id, hit.canonical_name, hit.status) for hit in report.hits],
    )
    emit(f"\n{len(report.hits)} match(es).")


@concept.command("show")
@click.argument("concept_id")
@lifecycle_options
@format_option
@click.pass_obj
def concept_show(
    obj: CliContext,
    concept_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    fmt: str,
) -> None:
    """Show one concept and its referring claims under the lifecycle policy."""

    repo = require_repo(obj)
    policy = lifecycle_policy(
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )
    with open_world(repo) as world_query:
        try:
            report = build_concept_view(world_query, concept_id, policy=policy)
        except ConceptViewUnknownConceptError:
            fail(f"Unknown concept: {concept_id}")

    if fmt == "json":
        emit_report_json(report)
        return
    emit(report.heading)
    if report.definition:
        emit(f"  definition: {report.definition}")
    emit(f"  form:       {report.form.sentence}")
    emit(f"  status:     {report.status.reason}")
    emit(f"  value:      {report.value_summary.sentence}")
    emit(f"  uncertainty:{report.uncertainty_summary.sentence}")
    for group in report.claim_groups:
        emit(f"  {group.claim_type}: {group.sentence}")

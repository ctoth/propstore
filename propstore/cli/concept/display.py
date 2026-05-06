from __future__ import annotations

import json

import click

from propstore.cli.output import emit, emit_table

from propstore.app.concepts import (
    ConceptDisplayError,
    ConceptListRequest,
    ConceptSearchRequest,
    ConceptShowRequest,
    ConceptSidecarMissingError,
    UnknownConceptError,
    list_concept_categories,
    list_concepts as run_list_concepts,
    search_concepts,
    show_concept,
)
from propstore.repository import Repository
from propstore.cli.helpers import fail
from propstore.cli.concept import (
    concept,
)


def _emit_report_json(report) -> None:
    emit(json.dumps(report.to_json(), indent=2))


@concept.command()
@click.argument("query")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def search(obj: dict, query: str, fmt: str) -> None:
    """Search concepts via the FTS5 index over canonical_name, aliases, definition, and CEL conditions."""
    try:
        report = search_concepts(
            obj["repo"],
            ConceptSearchRequest(query=query),
        )
    except ConceptSidecarMissingError as exc:
        raise click.ClickException(
            "concept search requires a built sidecar; run 'pks build' first"
        ) from exc

    if fmt == "json":
        _emit_report_json(report)
        return
    if report.hits:
        for hit in report.hits:
            snippet = hit.definition[:80]
            emit(f"  {hit.logical_id}  {hit.canonical_name}  — {snippet}")
    else:
        emit("No matches.")


# ── concept list ─────────────────────────────────────────────────────

@concept.command("list")
@click.option("--domain", default=None, help="Filter by domain")
@click.option("--status", default=None, help="Filter by status")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def list_concepts(
    obj: dict,
    domain: str | None,
    status: str | None,
    fmt: str,
) -> None:
    """List concepts, optionally filtered."""
    repo: Repository = obj["repo"]
    report = run_list_concepts(
        repo,
        ConceptListRequest(domain=domain, status=status),
    )
    if fmt == "json":
        _emit_report_json(report)
        return
    if not report.concepts_found:
        emit("No concepts directory found.")
        return

    emit_table(
        ("Handle", "Canonical name", "Status"),
        [
            (entry.handle, entry.canonical_name, f"[{entry.status}]")
            for entry in report.entries
        ],
    )


# ── concept add-value ────────────────────────────────────────────────


@concept.command("categories")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def categories(obj: dict, as_json: bool, fmt: str) -> None:
    """List all category concepts and their allowed values."""
    repo: Repository = obj["repo"]
    try:
        report = list_concept_categories(repo)
    except ConceptDisplayError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        emit(json.dumps(report.as_dict(), indent=2))
        return

    if fmt == "json":
        _emit_report_json(report)
        return
    if not report.entries:
        emit("No category concepts found.")
        return

    for entry in sorted(report.entries, key=lambda item: item.canonical_name):
        ext = " (extensible)" if entry.extensible else ""
        vals = ", ".join(entry.values)
        emit(f"{entry.canonical_name}{ext}: {vals}")


# ── concept show ─────────────────────────────────────────────────────

@concept.command()
@click.argument("concept_id_or_name")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def show(obj: dict, concept_id_or_name: str, fmt: str) -> None:
    """Show full concept YAML."""
    repo: Repository = obj["repo"]
    try:
        report = show_concept(
            repo,
            ConceptShowRequest(concept_id_or_name=concept_id_or_name),
        )
    except UnknownConceptError:
        if concept_id_or_name.startswith("align:"):
            fail(f"Concept alignment '{concept_id_or_name}' not found")
        fail(f"Concept '{concept_id_or_name}' not found")
    if fmt == "json":
        _emit_report_json(report)
        return
    emit(report.rendered)

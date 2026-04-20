"""pks form — subcommands for managing form definitions."""
from __future__ import annotations

import sys

import click

from propstore.cli.output import emit

from quire.documents import encode_document
from propstore.cli.helpers import EXIT_ERROR
from propstore.repository import Repository
from propstore.app.forms import (
    FormAddRequest,
    FormReferencedError,
    FormNotFoundError,
    FormWorkflowError,
    add_form,
    format_dims_col,
    list_form_items,
    remove_form,
    show_form,
    validate_forms,
)


@click.group()
def form() -> None:
    """Manage form definitions."""


# ── form list ────────────────────────────────────────────────────────

@form.command("list")
@click.option("--dims", "dims_filter", default=None,
              help="Filter by dimensions (e.g. M:1,L:1,T:-2). Implies showing dims column.")
@click.option("--show-dims", "show_dims_flag", is_flag=True, default=False,
              help="Show dimensions column.")
@click.pass_obj
def list_forms(obj: dict, dims_filter: str | None, show_dims_flag: bool) -> None:
    """List all available forms.

    With --show-dims: show dimensions column.
    With --dims M:1,L:1,T:-2: filter to forms matching those dimensions.
    """
    repo: Repository = obj["repo"]
    items = list_form_items(repo, dims_filter=dims_filter)
    if items is None:
        emit("No forms directory found.")
        return

    show_dims = show_dims_flag or dims_filter is not None
    for item in items:
        unit = item.unit_symbol or ""
        unit_col = f"  [{unit}]" if unit else ""
        if show_dims:
            dims_str = format_dims_col(item.dimensions, item.is_dimensionless)
            emit(f"  {item.name:30s}{unit_col:10s}  {dims_str}")
        else:
            emit(f"  {item.name:30s}{unit_col}")


# ── form show ────────────────────────────────────────────────────────

@form.command()
@click.argument("name")
@click.pass_obj
def show(obj: dict, name: str) -> None:
    """Show a form definition: raw YAML, unit conversions, and sidecar-derived algebra.

    Prints the form YAML, then a list of any declared unit conversions
    (multiplicative, affine, or logarithmic), and — if a sidecar has been
    built — appends the form algebra entries (decompositions derived from
    concept parameterizations, and forms that use this one).
    """
    repo: Repository = obj["repo"]
    try:
        report = show_form(repo, name)
    except FormNotFoundError:
        emit(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    emit(report.yaml_text)

    form_def = report.form
    if form_def and form_def.conversions:
        emit("Unit Conversions:")
        si = form_def.unit_symbol or "SI"
        for conv in form_def.conversions.values():
            if conv.type == "multiplicative":
                emit(f"  {conv.unit} \u2192 {si}  (\u00d7{conv.multiplier:g})")
            elif conv.type == "affine":
                emit(f"  {conv.unit} \u2192 {si}  (\u00d7{conv.multiplier:g} + {conv.offset:g}, affine)")
            elif conv.type == "logarithmic":
                emit(f"  {conv.unit} \u2192 {si}  (logarithmic, ref={conv.reference:g})")
            else:
                emit(f"  {conv.unit} \u2192 {si}  ({conv.type})")

    if report.decompositions or report.uses:
        emit("---")
        emit("# Form Algebra (derived from concept parameterizations)")
    if report.decompositions:
        emit("decompositions:")
        for entry in report.decompositions:
            emit(f"  - {name} = {' * '.join(entry.input_forms)}")
            if entry.source_formula:
                emit(
                    f"    from: {entry.source_formula} "
                    f"({entry.source_concept_id})"
                )
    if report.uses:
        emit("used_in:")
        for entry in report.uses:
            emit(f"  - {entry.output_form} = {' * '.join(entry.input_forms)}")


# ── form add ─────────────────────────────────────────────────────────

@form.command()
@click.option("--name", required=True, help="Form name (lowercase, underscored)")
@click.option("--unit", "unit_symbol", default=None, help="Primary unit symbol (e.g. Hz, Pa)")
@click.option("--qudt", default=None, help="QUDT IRI (e.g. qudt:HZ)")
@click.option("--base", default=None, help="Base type (e.g. ratio)")
@click.option("--dimensions", default=None, help="JSON dict of SI dimension exponents, e.g. '{\"T\": -1}'")
@click.option("--dimensionless", default=None, help="Whether the form is dimensionless (true/false)")
@click.option("--common-alternatives", default=None, help="JSON array of alternative unit conversions")
@click.option("--note", default=None, help="Human-readable note about this form")
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing")
@click.pass_obj
def add(
    obj: dict,
    name: str,
    unit_symbol: str | None,
    qudt: str | None,
    base: str | None,
    dimensions: str | None,
    dimensionless: str | None,
    common_alternatives: str | None,
    note: str | None,
    dry_run: bool,
) -> None:
    """Add a new form definition."""
    repo: Repository = obj["repo"]
    request = FormAddRequest(
        name=name,
        unit_symbol=unit_symbol,
        qudt=qudt,
        base=base,
        dimensions_json=dimensions,
        dimensionless=dimensionless,
        common_alternatives_json=common_alternatives,
        note=note,
    )
    try:
        report = add_form(repo, request, dry_run=dry_run)
    except FormWorkflowError as exc:
        emit(f"ERROR: {exc}", err=True)
        sys.exit(EXIT_ERROR)

    if not report.created:
        emit(f"Would create {report.path}")
        emit(encode_document(report.document).decode("utf-8"))
        return

    emit(f"Created {report.path}")


# ── form remove ──────────────────────────────────────────────────────

@form.command()
@click.argument("name")
@click.option("--force", is_flag=True, help="Remove even if concepts reference this form")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def remove(obj: dict, name: str, force: bool, dry_run: bool) -> None:
    """Remove a form definition."""
    repo: Repository = obj["repo"]
    try:
        report = remove_form(repo, name, force=force, dry_run=dry_run)
    except FormNotFoundError:
        emit(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)
    except FormReferencedError as exc:
        emit(f"ERROR: {exc}:", err=True)
        for ref in exc.references:
            emit(f"  {ref}", err=True)
        emit("Use --force to remove anyway.", err=True)
        sys.exit(EXIT_ERROR)

    if not report.removed:
        emit(f"Would remove {report.path}")
        if report.references:
            emit(f"  ({len(report.references)} concept(s) still reference this form)")
        return

    emit(f"Removed {report.path}")
    if report.references:
        emit(f"  WARNING: {len(report.references)} concept(s) still reference this form")


# ── form validate ────────────────────────────────────────────────────

@form.command()
@click.argument("name", required=False)
@click.pass_obj
def validate(obj: dict, name: str | None) -> None:
    """Validate form definitions (one or all).

    Checks that every form YAML has a valid name field and that forms
    referenced by concepts actually exist.
    """
    repo: Repository = obj["repo"]
    try:
        report = validate_forms(repo, name)
    except FormNotFoundError:
        emit(f"ERROR: Form '{name}' not found", err=True)
        sys.exit(EXIT_ERROR)

    if report is None:
        emit("No forms directory found.")
        return

    if not report.ok:
        for e in report.errors:
            emit(f"ERROR: {e}", err=True)
        sys.exit(EXIT_ERROR)

    emit(f"OK: {report.count} form(s) valid")

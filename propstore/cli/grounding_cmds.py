from __future__ import annotations

from typing import TYPE_CHECKING

import click

from propstore.cli.output import emit, emit_section

from propstore.app.grounding import (
    GroundingExplainRequest,
    GroundingInspectionError,
    GroundingQueryRequest,
    grounding_arguments as run_grounding_arguments,
    grounding_explain as run_grounding_explain,
    grounding_query as run_grounding_query,
    grounding_show as run_grounding_show,
    grounding_status as run_grounding_status,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@click.group()
def grounding() -> None:
    """Inspect the grounded rule theory directly."""


@grounding.command("status")
@click.pass_obj
def grounding_status(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = run_grounding_status(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"Predicate files: {len(report.surface.predicate_files)}")
    emit(f"Rule files: {len(report.surface.rule_files)}")
    emit(f"Grounding surface: {report.surface_state}")
    if report.message is not None:
        emit(report.message)
        return
    emit(f"Facts: {report.facts_count}")
    for section, count in report.section_counts:
        emit(f"  {section}: {count}")


@grounding.command("show")
@click.pass_obj
def grounding_show(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = run_grounding_show(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit_section(
        f"Facts ({len(report.facts)}):",
        report.facts if report.facts else ("<empty>",),
    )

    emit_section(
        f"Grounded rules ({len(report.rules)}):",
        (rule.text for rule in report.rules) if report.rules else ("<empty>",),
    )

    emit("Sections:")
    for section, lines in report.sections:
        emit(f"  {section}:")
        if not lines:
            emit("    <empty>")
            continue
        for line in lines:
            emit(f"    {line}")


@grounding.command("query")
@click.argument("atom")
@click.pass_obj
def grounding_query(obj: dict, atom: str) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = run_grounding_query(repo, GroundingQueryRequest(atom=atom))
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"{report.atom!r}")
    if report.matched_sections:
        emit(f"  status: {', '.join(report.matched_sections)}")
        return
    emit("  status: absent")


@grounding.command("arguments")
@click.pass_obj
def grounding_arguments(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = run_grounding_arguments(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit_section(
        f"Arguments ({len(report.arguments)}):",
        report.arguments if report.arguments else ("<empty>",),
    )


@grounding.command("explain")
@click.argument("atom")
@click.pass_obj
def grounding_explain(obj: dict, atom: str) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = run_grounding_explain(repo, GroundingExplainRequest(atom=atom))
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"{report.atom!r}")
    if report.matched_sections:
        emit(f"  status: {', '.join(report.matched_sections)}")
    else:
        emit("  status: absent")
    if report.explained_atom is not None and report.explained_atom != report.atom:
        emit(f"  explained atom: {report.explained_atom!r}")
    if report.message is not None:
        emit(report.message)
        return
    emit_section("Textual explanation:", report.prose.splitlines() if report.prose else ("<empty>",))
    emit_section("Dialectical tree:", report.tree.splitlines() if report.tree else ("<empty>",))

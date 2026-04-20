from __future__ import annotations

from typing import TYPE_CHECKING

import click

from propstore.cli.output import emit

from propstore.app.grounding import (
    GroundingInspectionError,
    inspect_grounding_arguments,
    inspect_grounding_query,
    inspect_grounding_show,
    inspect_grounding_status,
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
        report = inspect_grounding_status(repo)
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
        report = inspect_grounding_show(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"Facts ({len(report.facts)}):")
    if not report.facts:
        emit("  <empty>")
    else:
        for fact in report.facts:
            emit(f"  {fact}")

    emit(f"Grounded rules ({len(report.rules)}):")
    if not report.rules:
        emit("  <empty>")
    else:
        for rule in report.rules:
            emit(f"  {rule.text}")

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
        report = inspect_grounding_query(repo, atom)
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
        report = inspect_grounding_arguments(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"Arguments ({len(report.arguments)}):")
    if not report.arguments:
        emit("  <empty>")
        return
    for argument in report.arguments:
        emit(f"  {argument}")

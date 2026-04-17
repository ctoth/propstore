from __future__ import annotations

from typing import TYPE_CHECKING

import click

from propstore.grounding.inspection import (
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

    click.echo(f"Predicate files: {len(report.surface.predicate_files)}")
    click.echo(f"Rule files: {len(report.surface.rule_files)}")
    click.echo(f"Grounding surface: {report.surface_state}")
    if report.message is not None:
        click.echo(report.message)
        return
    click.echo(f"Facts: {report.facts_count}")
    for section, count in report.section_counts:
        click.echo(f"  {section}: {count}")


@grounding.command("show")
@click.pass_obj
def grounding_show(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = inspect_grounding_show(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Facts ({len(report.facts)}):")
    if not report.facts:
        click.echo("  <empty>")
    else:
        for fact in report.facts:
            click.echo(f"  {fact}")

    click.echo(f"Grounded rules ({len(report.rules)}):")
    if not report.rules:
        click.echo("  <empty>")
    else:
        for rule in report.rules:
            click.echo(f"  {rule.text}")

    click.echo("Sections:")
    for section, lines in report.sections:
        click.echo(f"  {section}:")
        if not lines:
            click.echo("    <empty>")
            continue
        for line in lines:
            click.echo(f"    {line}")


@grounding.command("query")
@click.argument("atom")
@click.pass_obj
def grounding_query(obj: dict, atom: str) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = inspect_grounding_query(repo, atom)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"{report.atom!r}")
    if report.matched_sections:
        click.echo(f"  status: {', '.join(report.matched_sections)}")
        return
    click.echo("  status: absent")


@grounding.command("arguments")
@click.pass_obj
def grounding_arguments(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    try:
        report = inspect_grounding_arguments(repo)
    except GroundingInspectionError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Arguments ({len(report.arguments)}):")
    if not report.arguments:
        click.echo("  <empty>")
        return
    for argument in report.arguments:
        click.echo(f"  {argument}")

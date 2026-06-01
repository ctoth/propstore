"""Worldline display CLI commands."""

from __future__ import annotations

import click

from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_section

from propstore.app.worldlines import (
    WorldlineDiffRequest,
    WorldlineShowRequest,
    WorldlineValidationError,
    WorldlineNotFoundError,
    diff_worldlines,
    list_worldlines,
    show_worldline,
)
from propstore.cli.worldline import worldline
from propstore.cli.worldline.rendering import (
    derivation_trace_lines,
    sensitivity_lines,
    target_value_lines,
)
from propstore.repository import Repository


@worldline.command("list")
@click.pass_obj
def worldline_list(obj: dict) -> None:
    """List all worldlines."""
    repo: Repository = obj["repo"]
    report = list_worldlines(repo)
    if not report.entries:
        emit("No worldlines.")
        return

    for entry in report.entries:
        if entry.error is not None:
            emit(f"  {entry.name}: ERROR — {entry.error}")
            continue
        status = entry.status or "pending"
        targets = ", ".join(entry.targets[:3])
        if len(entry.targets) > 3:
            targets += f" (+{len(entry.targets) - 3})"
        emit(f"  {entry.name}: {status} → {targets}")


@worldline.command("diff")
@click.argument("name_a")
@click.argument("name_b")
@click.pass_obj
def worldline_diff(obj: dict, name_a: str, name_b: str) -> None:
    """Compare two worldlines side by side."""
    repo: Repository = obj["repo"]
    try:
        report = diff_worldlines(
            repo,
            WorldlineDiffRequest(left_name=name_a, right_name=name_b),
        )
    except WorldlineNotFoundError as exc:
        fail(f"Worldline '{exc.name}' not found")
    except WorldlineValidationError as exc:
        fail(exc)

    emit(f"Comparing: {report.left_id} vs {report.right_id}")

    for difference in report.input_differences:
        emit(
            f"  {difference.label}: {dict(difference.left)} vs {dict(difference.right)}"
        )

    for difference in report.value_differences:
        emit(
            f"  {difference.target}: "
            f"{difference.left_value} ({difference.left_status}) → "
            f"{difference.right_value} ({difference.right_status})"
        )

    if not report.value_differences:
        emit("  No value differences.")

    if report.only_left_dependencies:
        emit(f"  Only in {report.left_id}: {', '.join(report.only_left_dependencies)}")
    if report.only_right_dependencies:
        emit(
            f"  Only in {report.right_id}: {', '.join(report.only_right_dependencies)}"
        )

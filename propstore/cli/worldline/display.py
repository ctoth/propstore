"""Worldline display CLI commands: ``show`` / ``list`` / ``diff``.

The persisted worldline is a dict-shaped charter
(:class:`~propstore.worldline.definition.WorldlineDefinition`); ``show``
reconstructs the typed compute forms one-way at render time via the package-owned
parsers (``WorldlineInputs.from_dict`` / ``WorldlineResult.from_dict`` /
``WorldlineRevisionQuery.from_dict``) — a boundary crossing that is a call, not a
conversion. The reconstructed forms are used only for presentation here.
"""
from __future__ import annotations

import click

from propstore.app.worldlines import (
    WorldlineDiffRequest,
    WorldlineNotFoundError,
    WorldlineShowRequest,
    WorldlineValidationError,
    diff_worldlines,
    list_worldlines,
    show_worldline,
)
from propstore.cli.helpers import CliContext, fail, require_repo
from propstore.cli.output import emit, emit_section
from propstore.cli.worldline import worldline
from propstore.cli.worldline.rendering import (
    derivation_trace_lines,
    sensitivity_lines,
    target_value_lines,
)
from propstore.worldline.query import (
    WorldlineResult,
    WorldlineRevisionQuery,
)


@worldline.command("show")
@click.argument("name")
@click.option("--check", is_flag=True, help="Check for staleness")
@click.pass_obj
def worldline_show(obj: CliContext, name: str, check: bool) -> None:
    """Show a worldline's question and (if materialized) its results."""
    repo = require_repo(obj)
    try:
        report = show_worldline(
            repo, WorldlineShowRequest(name=name, check_staleness=check)
        )
    except WorldlineNotFoundError:
        fail(f"Worldline '{name}' not found")

    wl = report.definition
    inputs = wl.inputs
    revision = WorldlineRevisionQuery.from_dict(wl.revision)
    results = WorldlineResult.from_dict(wl.results)

    emit(f"Worldline: {wl.name or wl.id}")
    if inputs.environment.bindings:
        emit(f"  Bindings: {dict(inputs.environment.bindings)}")
    if inputs.overrides:
        emit(f"  Overrides: {dict(inputs.overrides)}")
    if inputs.environment.context_id is not None:
        emit(f"  Context: {inputs.environment.context_id}")
    emit(f"  Targets: {list(wl.targets)}")

    if revision is not None:
        emit(f"  Revision query: {revision.operation}")
        if revision.atom is not None:
            emit(f"  Revision atom: {revision.atom.to_dict()}")
        if revision.target is not None:
            emit(f"  Revision target: {revision.target}")
        if revision.conflicts.targets_by_atom_id:
            emit(f"  Revision conflicts: {revision.conflicts.to_dict()}")
        if revision.operator is not None:
            emit(f"  Revision operator: {revision.operator}")

    if results is None:
        emit("  (not yet materialized — run 'pks worldline run' first)")
        return

    emit(f"  Computed: {results.computed}")

    if check:
        if report.staleness_unavailable:
            emit("  Cannot check staleness: sidecar not found")
        elif report.stale:
            emit("  STALE: upstream dependencies have changed")
        else:
            emit("  Fresh: dependencies unchanged")

    emit_section(
        "Results:",
        target_value_lines(results.values, include_details=True),
    )

    if results.steps:
        emit_section("Derivation trace:", derivation_trace_lines(results))

    sensitivity = tuple(sensitivity_lines(results))
    if sensitivity:
        emit_section("Sensitivity:", sensitivity)

    if results.argumentation is not None and results.argumentation.defeated:
        emit(f"Defeated claims: {', '.join(results.argumentation.defeated)}")

    if results.revision is not None:
        state = results.revision
        emit(f"Revision result: {state.operation or '?'}")
        if state.input_atom_id:
            emit(f"Input atom: {state.input_atom_id}")
        if state.target_atom_ids:
            emit(f"Target atoms: {', '.join(state.target_atom_ids)}")
        if state.error is not None:
            emit(f"Revision error: {state.error.value}")
        result_payload = state.result
        rejected = () if result_payload is None else result_payload.rejected_atom_ids
        if rejected:
            emit(f"Rejected atoms: {', '.join(rejected)}")
        accepted = () if result_payload is None else result_payload.accepted_atom_ids
        if accepted:
            emit(f"Accepted atoms: {', '.join(accepted)}")

    if results.dependencies.claims:
        emit(f"Dependencies: {', '.join(results.dependencies.claims)}")


@worldline.command("list")
@click.pass_obj
def worldline_list(obj: CliContext) -> None:
    """List all worldlines."""
    repo = require_repo(obj)
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
def worldline_diff(obj: CliContext, name_a: str, name_b: str) -> None:
    """Compare two worldlines side by side."""
    repo = require_repo(obj)
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
            f"  {difference.label}: "
            f"{dict(difference.left)} vs {dict(difference.right)}"
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
        emit(
            f"  Only in {report.left_id}: "
            f"{', '.join(report.only_left_dependencies)}"
        )
    if report.only_right_dependencies:
        emit(
            f"  Only in {report.right_id}: "
            f"{', '.join(report.only_right_dependencies)}"
        )

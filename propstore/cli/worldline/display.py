"""Worldline display CLI commands."""
from __future__ import annotations

import sys

import click

from propstore.cli.output import emit

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
from propstore.repository import Repository


@worldline.command("show")
@click.argument("name")
@click.option("--check", is_flag=True, help="Check for staleness")
@click.pass_obj
def worldline_show(obj: dict, name: str, check: bool) -> None:
    """Show a worldline's results."""
    repo: Repository = obj["repo"]
    try:
        report = show_worldline(repo, WorldlineShowRequest(name=name, check_staleness=check))
    except WorldlineNotFoundError:
        emit(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)
    wl = report.definition

    emit(f"Worldline: {wl.name or wl.id}")
    if wl.inputs.environment.bindings:
        emit(f"  Bindings: {dict(wl.inputs.environment.bindings)}")
    if wl.inputs.overrides:
        emit(f"  Overrides: {wl.inputs.overrides}")
    if wl.inputs.environment.context_id:
        emit(f"  Context: {wl.inputs.environment.context_id}")
    emit(f"  Targets: {wl.targets}")
    if wl.revision is not None:
        emit(f"  Revision query: {wl.revision.operation}")
        if wl.revision.atom is not None:
            emit(f"  Revision atom: {wl.revision.atom.to_dict()}")
        if wl.revision.target is not None:
            emit(f"  Revision target: {wl.revision.target}")
        if wl.revision.conflicts.targets_by_atom_id:
            emit(f"  Revision conflicts: {wl.revision.conflicts.to_dict()}")
        if wl.revision.operator is not None:
            emit(f"  Revision operator: {wl.revision.operator}")

    if wl.results is None:
        emit("  (not yet materialized — run 'pks worldline run' first)")
        return

    emit(f"  Computed: {wl.results.computed}")

    if check:
        if report.staleness_unavailable:
            emit("  ? Cannot check staleness — sidecar not found")
        elif report.stale:
            emit("  ⚠ STALE — upstream dependencies have changed")
        else:
            emit("  ✓ Fresh — dependencies unchanged")

    emit("Results:")
    for target, val in wl.results.values.items():
        status = val.status
        value = val.value
        source = val.source or ""
        if value is not None:
            line = f"  {target}: {value} ({status}, {source})"
            if val.formula:
                line += f" via {val.formula}"
            if val.winning_claim_id:
                line += f" [winner: {val.winning_claim_id}]"
            emit(line)
        else:
            reason = val.reason or ""
            emit(f"  {target}: {status} — {reason}")

    if wl.results.steps:
        emit("Derivation trace:")
        for step in wl.results.steps:
            source = step.source
            value = step.value
            concept = step.concept
            extra = ""
            if step.claim_id:
                extra = f" [claim: {step.claim_id}]"
            if step.formula:
                extra = f" via {step.formula}"
            emit(f"  {concept} = {value} ({source}){extra}")

    if wl.results.sensitivity:
        emit("Sensitivity:")
        for concept, outcome in wl.results.sensitivity.targets.items():
            if outcome.error is not None:
                emit(f"  {concept}: ERROR — {outcome.error}")
                continue
            for entry in outcome.entries:
                elast = entry.elasticity
                deriv = entry.partial_derivative
                inp = entry.input_name
                emit(f"  {concept}: d/d({inp}) = {deriv}, elasticity = {elast}")

    if wl.results.argumentation:
        defeated = wl.results.argumentation.defeated
        if defeated:
            emit(f"Defeated claims: {', '.join(defeated)}")

    if wl.results.revision:
        revision = wl.results.revision
        emit(f"Revision result: {revision.operation or '?'}")
        if revision.input_atom_id:
            emit(f"Input atom: {revision.input_atom_id}")
        target_atom_ids = revision.target_atom_ids
        if target_atom_ids:
            emit(f"Target atoms: {', '.join(target_atom_ids)}")
        if revision.error:
            emit(f"Revision error: {revision.error}")
        result_payload = revision.result
        rejected = () if result_payload is None else result_payload.rejected_atom_ids
        if rejected:
            emit(f"Rejected atoms: {', '.join(rejected)}")
        accepted = () if result_payload is None else result_payload.accepted_atom_ids
        if accepted:
            emit(f"Accepted atoms: {', '.join(accepted)}")

    if wl.results.dependencies.claims:
        emit(f"Dependencies: {', '.join(wl.results.dependencies.claims)}")


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
        emit(f"ERROR: Worldline '{exc.name}' not found", err=True)
        sys.exit(1)
    except WorldlineValidationError as exc:
        emit(f"ERROR: {exc}", err=True)
        sys.exit(1)

    emit(f"Comparing: {report.left_id} vs {report.right_id}")

    for difference in report.input_differences:
        emit(f"  {difference.label}: {dict(difference.left)} vs {dict(difference.right)}")

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
        emit(f"  Only in {report.right_id}: {', '.join(report.only_right_dependencies)}")


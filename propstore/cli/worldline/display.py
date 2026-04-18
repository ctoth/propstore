"""Worldline display CLI commands."""
from __future__ import annotations

import sys

import click

from quire.documents import DocumentSchemaError
from propstore.cli.helpers import open_world_model
from propstore.cli.worldline import _load_worldline_definition, worldline
from propstore.repository import Repository


@worldline.command("show")
@click.argument("name")
@click.option("--check", is_flag=True, help="Check for staleness")
@click.pass_obj
def worldline_show(obj: dict, name: str, check: bool) -> None:
    """Show a worldline's results."""
    repo: Repository = obj["repo"]
    try:
        wl = _load_worldline_definition(repo, name)
    except FileNotFoundError:
        click.echo(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)

    click.echo(f"Worldline: {wl.name or wl.id}")
    if wl.inputs.environment.bindings:
        click.echo(f"  Bindings: {dict(wl.inputs.environment.bindings)}")
    if wl.inputs.overrides:
        click.echo(f"  Overrides: {wl.inputs.overrides}")
    if wl.inputs.environment.context_id:
        click.echo(f"  Context: {wl.inputs.environment.context_id}")
    click.echo(f"  Targets: {wl.targets}")
    if wl.revision is not None:
        click.echo(f"  Revision query: {wl.revision.operation}")
        if wl.revision.atom is not None:
            click.echo(f"  Revision atom: {wl.revision.atom.to_dict()}")
        if wl.revision.target is not None:
            click.echo(f"  Revision target: {wl.revision.target}")
        if wl.revision.conflicts.targets_by_atom_id:
            click.echo(f"  Revision conflicts: {wl.revision.conflicts.to_dict()}")
        if wl.revision.operator is not None:
            click.echo(f"  Revision operator: {wl.revision.operator}")

    if wl.results is None:
        click.echo("  (not yet materialized — run 'pks worldline run' first)")
        return

    click.echo(f"  Computed: {wl.results.computed}")

    if check:
        try:
            with open_world_model(repo) as wm:
                stale = wl.is_stale(wm)
        except SystemExit:
            click.echo("  ? Cannot check staleness — sidecar not found")
        else:
            if stale:
                click.echo("  ⚠ STALE — upstream dependencies have changed")
            else:
                click.echo("  ✓ Fresh — dependencies unchanged")

    click.echo("Results:")
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
            click.echo(line)
        else:
            reason = val.reason or ""
            click.echo(f"  {target}: {status} — {reason}")

    if wl.results.steps:
        click.echo("Derivation trace:")
        for step in wl.results.steps:
            source = step.source
            value = step.value
            concept = step.concept
            extra = ""
            if step.claim_id:
                extra = f" [claim: {step.claim_id}]"
            if step.formula:
                extra = f" via {step.formula}"
            click.echo(f"  {concept} = {value} ({source}){extra}")

    if wl.results.sensitivity:
        click.echo("Sensitivity:")
        for concept, outcome in wl.results.sensitivity.targets.items():
            if outcome.error is not None:
                click.echo(f"  {concept}: ERROR — {outcome.error}")
                continue
            for entry in outcome.entries:
                elast = entry.elasticity
                deriv = entry.partial_derivative
                inp = entry.input_name
                click.echo(f"  {concept}: d/d({inp}) = {deriv}, elasticity = {elast}")

    if wl.results.argumentation:
        defeated = wl.results.argumentation.defeated
        if defeated:
            click.echo(f"Defeated claims: {', '.join(defeated)}")

    if wl.results.revision:
        revision = wl.results.revision
        click.echo(f"Revision result: {revision.operation or '?'}")
        if revision.input_atom_id:
            click.echo(f"Input atom: {revision.input_atom_id}")
        target_atom_ids = revision.target_atom_ids
        if target_atom_ids:
            click.echo(f"Target atoms: {', '.join(target_atom_ids)}")
        if revision.error:
            click.echo(f"Revision error: {revision.error}")
        result_payload = revision.result
        rejected = () if result_payload is None else result_payload.rejected_atom_ids
        if rejected:
            click.echo(f"Rejected atoms: {', '.join(rejected)}")
        accepted = () if result_payload is None else result_payload.accepted_atom_ids
        if accepted:
            click.echo(f"Accepted atoms: {', '.join(accepted)}")

    if wl.results.dependencies.claims:
        click.echo(f"Dependencies: {', '.join(wl.results.dependencies.claims)}")


@worldline.command("list")
@click.pass_obj
def worldline_list(obj: dict) -> None:
    """List all worldlines."""
    repo: Repository = obj["repo"]
    refs = repo.families.worldlines.list()
    if not refs:
        click.echo("No worldlines.")
        return

    for ref in refs:
        try:
            wl = _load_worldline_definition(repo, ref.name)
            status = "materialized" if wl.results else "pending"
            targets = ", ".join(wl.targets[:3])
            if len(wl.targets) > 3:
                targets += f" (+{len(wl.targets) - 3})"
            click.echo(f"  {wl.id}: {status} → {targets}")
        except DocumentSchemaError as e:
            click.echo(f"  {ref.name}: ERROR — {e}")
        except Exception as e:
            click.echo(f"  {ref.name}: ERROR — {e}")


@worldline.command("diff")
@click.argument("name_a")
@click.argument("name_b")
@click.pass_obj
def worldline_diff(obj: dict, name_a: str, name_b: str) -> None:
    """Compare two worldlines side by side."""
    repo: Repository = obj["repo"]
    try:
        wl_a = _load_worldline_definition(repo, name_a)
    except FileNotFoundError:
        click.echo(f"ERROR: Worldline '{name_a}' not found", err=True)
        sys.exit(1)
    try:
        wl_b = _load_worldline_definition(repo, name_b)
    except FileNotFoundError:
        click.echo(f"ERROR: Worldline '{name_b}' not found", err=True)
        sys.exit(1)

    if wl_a.results is None or wl_b.results is None:
        click.echo("ERROR: Both worldlines must be materialized first", err=True)
        sys.exit(1)

    click.echo(f"Comparing: {wl_a.id} vs {wl_b.id}")

    # Show input differences
    if wl_a.inputs.environment.bindings != wl_b.inputs.environment.bindings:
        click.echo(
            f"  Bindings: {dict(wl_a.inputs.environment.bindings)} vs "
            f"{dict(wl_b.inputs.environment.bindings)}"
        )
    if wl_a.inputs.overrides != wl_b.inputs.overrides:
        click.echo(f"  Overrides: {wl_a.inputs.overrides} vs {wl_b.inputs.overrides}")

    # Show value differences
    all_targets = set(wl_a.results.values.keys()) | set(wl_b.results.values.keys())
    any_diff = False
    for target in sorted(all_targets):
        val_a = wl_a.results.values.get(target)
        val_b = wl_b.results.values.get(target)
        v_a = None if val_a is None else val_a.value
        v_b = None if val_b is None else val_b.value
        if v_a != v_b:
            any_diff = True
            s_a = "absent" if val_a is None else val_a.status
            s_b = "absent" if val_b is None else val_b.status
            click.echo(f"  {target}: {v_a} ({s_a}) → {v_b} ({s_b})")

    if not any_diff:
        click.echo("  No value differences.")

    # Show dependency differences
    deps_a = set(wl_a.results.dependencies.claims)
    deps_b = set(wl_b.results.dependencies.claims)
    only_a = deps_a - deps_b
    only_b = deps_b - deps_a
    if only_a:
        click.echo(f"  Only in {wl_a.id}: {', '.join(sorted(only_a))}")
    if only_b:
        click.echo(f"  Only in {wl_b.id}: {', '.join(sorted(only_b))}")


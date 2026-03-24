"""pks worldline — CLI commands for materialized query artifacts."""
from __future__ import annotations

import sys
from typing import Any

import click
import yaml

from propstore.cli.repository import Repository


def _parse_kv_args(args: tuple[str, ...]) -> dict[str, Any]:
    """Parse key=value arguments into a dict with type coercion."""
    from propstore.cli.helpers import parse_kv_pairs

    parsed, remaining = parse_kv_pairs(args, coerce=True)
    for r in remaining:
        click.echo(f"WARNING: ignoring argument without '=': {r}", err=True)
    return parsed


@click.group()
@click.pass_obj
def worldline(obj: dict) -> None:
    """Materialized query artifacts — traced paths through the knowledge space."""


@worldline.command("create")
@click.argument("name")
@click.option("--bind", "bindings", multiple=True, help="Condition binding (key=value)")
@click.option("--with", "overrides", multiple=True, help="Value override (concept=value)")
@click.option("--target", "targets", multiple=True, required=True, help="Target concept to derive/resolve")
@click.option("--strategy", default=None, type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--context", default=None, help="Context to scope the query")
@click.pass_obj
def worldline_create(obj: dict, name: str, bindings: tuple[str, ...],
                     overrides: tuple[str, ...], targets: tuple[str, ...],
                     strategy: str | None, context: str | None) -> None:
    """Create a worldline definition (question only, no results yet)."""
    from propstore.worldline import WorldlineDefinition

    repo: Repository = obj["repo"]
    wl_dir = repo.worldlines_dir
    wl_dir.mkdir(parents=True, exist_ok=True)

    path = wl_dir / f"{name}.yaml"
    if path.exists():
        click.echo(f"ERROR: Worldline '{name}' already exists at {path}", err=True)
        sys.exit(1)

    bind_dict = _parse_kv_args(bindings)
    override_dict: dict[str, float | str] = {}
    for k, v in _parse_kv_args(overrides).items():
        try:
            override_dict[k] = float(v)
        except ValueError:
            override_dict[k] = v

    definition = {
        "id": name,
        "name": name,
        "targets": list(targets),
    }

    inputs: dict = {}
    if bind_dict:
        inputs["bindings"] = bind_dict
    if override_dict:
        inputs["overrides"] = override_dict
    if context:
        inputs["context"] = context
    if inputs:
        definition["inputs"] = inputs

    if strategy:
        definition["policy"] = {"strategy": strategy}

    wl = WorldlineDefinition.from_dict(definition)
    wl.to_file(path)
    click.echo(f"Created worldline '{name}' at {path}")


@worldline.command("run")
@click.argument("name")
@click.option("--bind", "bindings", multiple=True, help="Condition binding (key=value)")
@click.option("--with", "overrides", multiple=True, help="Value override (concept=value)")
@click.option("--target", "targets", multiple=True, help="Target concept")
@click.option("--strategy", default=None, type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--context", default=None, help="Context scope")
@click.pass_obj
def worldline_run(obj: dict, name: str, bindings: tuple[str, ...],
                  overrides: tuple[str, ...], targets: tuple[str, ...],
                  strategy: str | None, context: str | None) -> None:
    """Run (materialize) a worldline. Creates it first if it doesn't exist."""
    from propstore.world import WorldModel
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline_runner import run_worldline

    repo: Repository = obj["repo"]
    wl_dir = repo.worldlines_dir
    wl_dir.mkdir(parents=True, exist_ok=True)
    path = wl_dir / f"{name}.yaml"

    # If file exists, load it; otherwise create from CLI args
    if path.exists():
        wl = WorldlineDefinition.from_file(path)
    else:
        if not targets:
            click.echo("ERROR: --target required when creating a new worldline", err=True)
            sys.exit(1)

        bind_dict = _parse_kv_args(bindings)
        override_dict: dict[str, float | str] = {}
        for k, v in _parse_kv_args(overrides).items():
            try:
                override_dict[k] = float(v)
            except ValueError:
                override_dict[k] = v

        definition: dict = {
            "id": name,
            "name": name,
            "targets": list(targets),
        }
        inputs: dict = {}
        if bind_dict:
            inputs["bindings"] = bind_dict
        if override_dict:
            inputs["overrides"] = override_dict
        if context:
            inputs["context"] = context
        if inputs:
            definition["inputs"] = inputs
        if strategy:
            definition["policy"] = {"strategy": strategy}

        wl = WorldlineDefinition.from_dict(definition)

    # Materialize
    try:
        wm = WorldModel(repo)
    except FileNotFoundError:
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    result = run_worldline(wl, wm)
    wl.results = result
    wl.to_file(path)
    wm.close()

    click.echo(f"Worldline '{name}' materialized ({len(result.values)} targets)")
    for target, val in result.values.items():
        status = val.get("status", "?")
        value = val.get("value")
        source = val.get("source", "")
        if value is not None:
            click.echo(f"  {target}: {value} ({status}, {source})")
        else:
            reason = val.get("reason", "")
            click.echo(f"  {target}: {status} — {reason}")


@worldline.command("show")
@click.argument("name")
@click.option("--check", is_flag=True, help="Check for staleness")
@click.pass_obj
def worldline_show(obj: dict, name: str, check: bool) -> None:
    """Show a worldline's results."""
    from propstore.worldline import WorldlineDefinition

    repo: Repository = obj["repo"]
    path = repo.worldlines_dir / f"{name}.yaml"
    if not path.exists():
        click.echo(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)

    wl = WorldlineDefinition.from_file(path)

    click.echo(f"Worldline: {wl.name or wl.id}")
    if wl.inputs.bindings:
        click.echo(f"  Bindings: {wl.inputs.bindings}")
    if wl.inputs.overrides:
        click.echo(f"  Overrides: {wl.inputs.overrides}")
    if wl.inputs.context:
        click.echo(f"  Context: {wl.inputs.context}")
    click.echo(f"  Targets: {wl.targets}")

    if wl.results is None:
        click.echo("  (not yet materialized — run 'pks worldline run' first)")
        return

    click.echo(f"  Computed: {wl.results.computed}")

    if check:
        from propstore.world import WorldModel
        try:
            wm = WorldModel(repo)
            stale = wl.is_stale(wm)
            wm.close()
            if stale:
                click.echo("  ⚠ STALE — upstream dependencies have changed")
            else:
                click.echo("  ✓ Fresh — dependencies unchanged")
        except FileNotFoundError:
            click.echo("  ? Cannot check staleness — sidecar not found")

    click.echo("Results:")
    for target, val in wl.results.values.items():
        status = val.get("status", "?")
        value = val.get("value")
        source = val.get("source", "")
        if value is not None:
            line = f"  {target}: {value} ({status}, {source})"
            if val.get("formula"):
                line += f" via {val['formula']}"
            if val.get("winning_claim_id"):
                line += f" [winner: {val['winning_claim_id']}]"
            click.echo(line)
        else:
            reason = val.get("reason", "")
            click.echo(f"  {target}: {status} — {reason}")

    if wl.results.steps:
        click.echo("Derivation trace:")
        for step in wl.results.steps:
            source = step.get("source", "?")
            value = step.get("value")
            concept = step.get("concept", "?")
            extra = ""
            if step.get("claim_id"):
                extra = f" [claim: {step['claim_id']}]"
            if step.get("formula"):
                extra = f" via {step['formula']}"
            click.echo(f"  {concept} = {value} ({source}){extra}")

    if wl.results.sensitivity:
        click.echo("Sensitivity:")
        for concept, entries in wl.results.sensitivity.items():
            for entry in entries:
                elast = entry.get("elasticity")
                deriv = entry.get("partial_derivative")
                inp = entry.get("input", "?")
                click.echo(f"  {concept}: d/d({inp}) = {deriv}, elasticity = {elast}")

    if wl.results.argumentation:
        defeated = wl.results.argumentation.get("defeated", [])
        if defeated:
            click.echo(f"Defeated claims: {', '.join(defeated)}")

    if wl.results.dependencies.get("claims"):
        click.echo(f"Dependencies: {', '.join(wl.results.dependencies['claims'])}")


@worldline.command("list")
@click.pass_obj
def worldline_list(obj: dict) -> None:
    """List all worldlines."""
    from propstore.worldline import WorldlineDefinition

    repo: Repository = obj["repo"]
    wl_dir = repo.worldlines_dir
    if not wl_dir.exists():
        click.echo("No worldlines directory.")
        return

    files = sorted(wl_dir.glob("*.yaml"))
    if not files:
        click.echo("No worldlines.")
        return

    for f in files:
        try:
            wl = WorldlineDefinition.from_file(f)
            status = "materialized" if wl.results else "pending"
            targets = ", ".join(wl.targets[:3])
            if len(wl.targets) > 3:
                targets += f" (+{len(wl.targets) - 3})"
            click.echo(f"  {wl.id}: {status} → {targets}")
        except Exception as e:
            click.echo(f"  {f.stem}: ERROR — {e}")


@worldline.command("diff")
@click.argument("name_a")
@click.argument("name_b")
@click.pass_obj
def worldline_diff(obj: dict, name_a: str, name_b: str) -> None:
    """Compare two worldlines side by side."""
    from propstore.worldline import WorldlineDefinition

    repo: Repository = obj["repo"]
    wl_dir = repo.worldlines_dir

    path_a = wl_dir / f"{name_a}.yaml"
    path_b = wl_dir / f"{name_b}.yaml"

    if not path_a.exists():
        click.echo(f"ERROR: Worldline '{name_a}' not found", err=True)
        sys.exit(1)
    if not path_b.exists():
        click.echo(f"ERROR: Worldline '{name_b}' not found", err=True)
        sys.exit(1)

    wl_a = WorldlineDefinition.from_file(path_a)
    wl_b = WorldlineDefinition.from_file(path_b)

    if wl_a.results is None or wl_b.results is None:
        click.echo("ERROR: Both worldlines must be materialized first", err=True)
        sys.exit(1)

    click.echo(f"Comparing: {wl_a.id} vs {wl_b.id}")

    # Show input differences
    if wl_a.inputs.bindings != wl_b.inputs.bindings:
        click.echo(f"  Bindings: {wl_a.inputs.bindings} vs {wl_b.inputs.bindings}")
    if wl_a.inputs.overrides != wl_b.inputs.overrides:
        click.echo(f"  Overrides: {wl_a.inputs.overrides} vs {wl_b.inputs.overrides}")

    # Show value differences
    all_targets = set(wl_a.results.values.keys()) | set(wl_b.results.values.keys())
    any_diff = False
    for target in sorted(all_targets):
        val_a = wl_a.results.values.get(target, {})
        val_b = wl_b.results.values.get(target, {})
        v_a = val_a.get("value")
        v_b = val_b.get("value")
        if v_a != v_b:
            any_diff = True
            s_a = val_a.get("status", "absent")
            s_b = val_b.get("status", "absent")
            click.echo(f"  {target}: {v_a} ({s_a}) → {v_b} ({s_b})")

    if not any_diff:
        click.echo("  No value differences.")

    # Show dependency differences
    deps_a = set(wl_a.results.dependencies.get("claims", []))
    deps_b = set(wl_b.results.dependencies.get("claims", []))
    only_a = deps_a - deps_b
    only_b = deps_b - deps_a
    if only_a:
        click.echo(f"  Only in {wl_a.id}: {', '.join(sorted(only_a))}")
    if only_b:
        click.echo(f"  Only in {wl_b.id}: {', '.join(sorted(only_b))}")


@worldline.command("refresh")
@click.argument("name")
@click.pass_obj
def worldline_refresh(obj: dict, name: str) -> None:
    """Re-run a worldline with current knowledge."""
    # Delegate to run
    ctx = click.get_current_context()
    ctx.invoke(worldline_run, name=name, bindings=(), overrides=(), targets=(), strategy=None, context=None)


@worldline.command("delete")
@click.argument("name")
@click.pass_obj
def worldline_delete(obj: dict, name: str) -> None:
    """Delete a worldline."""
    repo: Repository = obj["repo"]
    path = repo.worldlines_dir / f"{name}.yaml"
    if not path.exists():
        click.echo(f"ERROR: Worldline '{name}' not found", err=True)
        sys.exit(1)
    path.unlink()
    click.echo(f"Deleted worldline '{name}'")

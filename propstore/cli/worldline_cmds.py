"""pks worldline — CLI commands for materialized query artifacts."""
from __future__ import annotations

import json
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


def _build_policy_dict(
    strategy: str | None,
    reasoning_backend: str,
    semantics: str,
    set_comparison: str,
    link_principle: str,
    decision_criterion: str,
    pessimism_index: float,
    praf_strategy: str,
    praf_epsilon: float,
    praf_confidence: float,
    praf_seed: int | None,
) -> dict[str, Any] | None:
    """Build a policy dict from CLI flags, omitting defaults.

    Returns None if no policy fields differ from RenderPolicy defaults.
    """
    policy: dict[str, Any] = {}
    if strategy:
        policy["strategy"] = strategy
    if reasoning_backend != "claim_graph":
        policy["reasoning_backend"] = reasoning_backend
    if semantics != "grounded":
        policy["semantics"] = semantics
    if set_comparison != "elitist":
        policy["comparison"] = set_comparison
    if link_principle != "last":
        policy["link"] = link_principle
    if decision_criterion != "pignistic":
        policy["decision_criterion"] = decision_criterion
    if pessimism_index != 0.5:
        policy["pessimism_index"] = pessimism_index
    if praf_strategy != "auto":
        policy["praf_strategy"] = praf_strategy
    if praf_epsilon != 0.01:
        policy["praf_mc_epsilon"] = praf_epsilon
    if praf_confidence != 0.95:
        policy["praf_mc_confidence"] = praf_confidence
    if praf_seed is not None:
        policy["praf_mc_seed"] = praf_seed
    return policy or None


# Shared click options for reasoning backend configuration.
_REASONING_OPTIONS = [
    click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
                 type=click.Choice(["claim_graph", "structured_projection", "aspic", "atms", "praf"]),
                 help="Argumentation backend (default: claim_graph)"),
    click.option("--semantics", default="grounded",
                 type=click.Choice(["grounded", "preferred", "stable"]),
                 help="Argumentation semantics (default: grounded)"),
    click.option("--set-comparison", "set_comparison", default="elitist",
                 type=click.Choice(["elitist", "democratic"]),
                 help="Set comparison for preference ordering (default: elitist)"),
    click.option("--link-principle", "link_principle", default="last",
                 type=click.Choice(["last", "weakest"]),
                 help="ASPIC+ link principle (default: last)"),
    click.option("--decision-criterion", "decision_criterion", default="pignistic",
                 type=click.Choice(["pignistic", "lower_bound", "upper_bound", "hurwicz"]),
                 help="Decision criterion for opinion interpretation (default: pignistic)"),
    click.option("--pessimism-index", "pessimism_index", default=0.5,
                 type=float, help="Hurwicz pessimism index (default: 0.5)"),
    click.option("--praf-strategy", "praf_strategy", default="auto",
                 type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
                 help="PrAF computation strategy (default: auto)"),
    click.option("--praf-epsilon", "praf_epsilon", default=0.01,
                 type=float, help="PrAF MC error tolerance (default: 0.01)"),
    click.option("--praf-confidence", "praf_confidence", default=0.95,
                 type=float, help="PrAF MC confidence level (default: 0.95)"),
    click.option("--praf-seed", "praf_seed", default=None,
                 type=int, help="PrAF MC RNG seed (default: random)"),
]


def _apply_reasoning_options(func):
    """Apply all reasoning backend click options to a command."""
    for option in reversed(_REASONING_OPTIONS):
        func = option(func)
    return func


_REVISION_OPTIONS = [
    click.option("--revision-operation", "revision_operation", default=None,
                 type=click.Choice(["expand", "contract", "revise", "iterated_revise"]),
                 help="Optional revision operation to record/run with this worldline"),
    click.option("--revision-atom", "revision_atom", default=None,
                 help="Revision atom as JSON mapping"),
    click.option("--revision-target", "revision_target", default=None,
                 help="Revision target for contract"),
    click.option("--revision-conflict", "revision_conflicts", multiple=True,
                 help="Revision conflict mapping as atom_id=target[,target...]"),
    click.option("--revision-operator", "revision_operator", default=None,
                 type=click.Choice(["restrained", "lexicographic"]),
                 help="Iterated revision operator family"),
]


def _apply_revision_options(func):
    for option in reversed(_REVISION_OPTIONS):
        func = option(func)
    return func


def _parse_revision_atom(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --revision-atom JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise click.ClickException("--revision-atom must decode to a JSON object")
    return parsed


def _parse_revision_conflicts(raw_conflicts: tuple[str, ...]) -> dict[str, list[str]]:
    conflicts: dict[str, list[str]] = {}
    for entry in raw_conflicts:
        atom_id, sep, targets = entry.partition("=")
        if not sep:
            raise click.ClickException(
                "Invalid --revision-conflict; expected atom_id=target[,target...]",
            )
        parsed_targets = [target.strip() for target in targets.split(",") if target.strip()]
        conflicts[str(atom_id)] = parsed_targets
    return conflicts


def _build_revision_dict(
    revision_operation: str | None,
    revision_atom: str | None,
    revision_target: str | None,
    revision_conflicts: tuple[str, ...],
    revision_operator: str | None,
) -> dict[str, Any] | None:
    if revision_operation is None:
        return None

    parsed_atom = _parse_revision_atom(revision_atom)
    parsed_conflicts = _parse_revision_conflicts(revision_conflicts)

    if revision_operation in {"expand", "revise", "iterated_revise"} and parsed_atom is None:
        raise click.ClickException(f"--revision-atom is required for {revision_operation}")
    if revision_operation == "contract" and revision_target is None:
        raise click.ClickException("--revision-target is required for contract")
    if revision_operation == "iterated_revise" and revision_operator is None:
        raise click.ClickException("--revision-operator is required for iterated_revise")

    revision: dict[str, Any] = {
        "operation": revision_operation,
    }
    if parsed_atom is not None:
        revision["atom"] = parsed_atom
    if revision_target is not None:
        revision["target"] = revision_target
    if parsed_conflicts:
        revision["conflicts"] = parsed_conflicts
    if revision_operator is not None:
        revision["operator"] = revision_operator
    return revision


@worldline.command("create")
@click.argument("name")
@click.option("--bind", "bindings", multiple=True, help="Condition binding (key=value)")
@click.option("--with", "overrides", multiple=True, help="Value override (concept=value)")
@click.option("--target", "targets", multiple=True, required=True, help="Target concept to derive/resolve")
@click.option("--strategy", default=None, type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--context", default=None, help="Context to scope the query")
@_apply_reasoning_options
@_apply_revision_options
@click.pass_obj
def worldline_create(obj: dict, name: str, bindings: tuple[str, ...],
                     overrides: tuple[str, ...], targets: tuple[str, ...],
                     strategy: str | None, context: str | None,
                     reasoning_backend: str, semantics: str,
                     set_comparison: str, link_principle: str, decision_criterion: str,
                     pessimism_index: float, praf_strategy: str,
                     praf_epsilon: float, praf_confidence: float,
                     praf_seed: int | None, revision_operation: str | None,
                     revision_atom: str | None, revision_target: str | None,
                     revision_conflicts: tuple[str, ...], revision_operator: str | None) -> None:
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
        inputs["context_id"] = context
    if inputs:
        definition["inputs"] = inputs

    policy = _build_policy_dict(
        strategy, reasoning_backend, semantics, set_comparison,
        link_principle,
        decision_criterion, pessimism_index, praf_strategy,
        praf_epsilon, praf_confidence, praf_seed,
    )
    if policy:
        definition["policy"] = policy

    revision = _build_revision_dict(
        revision_operation,
        revision_atom,
        revision_target,
        revision_conflicts,
        revision_operator,
    )
    if revision:
        definition["revision"] = revision

    wl = WorldlineDefinition.from_dict(definition)
    wl.to_file(path)

    git = repo.git
    if git is not None:
        rel_path = path.relative_to(repo.root).as_posix()
        git.commit_files({rel_path: path.read_bytes()}, f"Create worldline: {name}")
        git.sync_worktree()

    click.echo(f"Created worldline '{name}' at {path}")


@worldline.command("run")
@click.argument("name")
@click.option("--bind", "bindings", multiple=True, help="Condition binding (key=value)")
@click.option("--with", "overrides", multiple=True, help="Value override (concept=value)")
@click.option("--target", "targets", multiple=True, help="Target concept")
@click.option("--strategy", default=None, type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--context", default=None, help="Context scope")
@_apply_reasoning_options
@_apply_revision_options
@click.pass_obj
def worldline_run(obj: dict, name: str, bindings: tuple[str, ...],
                  overrides: tuple[str, ...], targets: tuple[str, ...],
                  strategy: str | None, context: str | None,
                  reasoning_backend: str, semantics: str,
                  set_comparison: str, link_principle: str, decision_criterion: str,
                  pessimism_index: float, praf_strategy: str,
                  praf_epsilon: float, praf_confidence: float,
                  praf_seed: int | None, revision_operation: str | None,
                  revision_atom: str | None, revision_target: str | None,
                  revision_conflicts: tuple[str, ...], revision_operator: str | None) -> None:
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
            inputs["context_id"] = context
        if inputs:
            definition["inputs"] = inputs

        policy = _build_policy_dict(
            strategy, reasoning_backend, semantics, set_comparison,
            link_principle,
            decision_criterion, pessimism_index, praf_strategy,
            praf_epsilon, praf_confidence, praf_seed,
        )
        if policy:
            definition["policy"] = policy

        revision = _build_revision_dict(
            revision_operation,
            revision_atom,
            revision_target,
            revision_conflicts,
            revision_operator,
        )
        if revision:
            definition["revision"] = revision

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
            click.echo(f"  Revision atom: {wl.revision.atom}")
        if wl.revision.target is not None:
            click.echo(f"  Revision target: {wl.revision.target}")
        if wl.revision.conflicts:
            click.echo(f"  Revision conflicts: {wl.revision.conflicts}")
        if wl.revision.operator is not None:
            click.echo(f"  Revision operator: {wl.revision.operator}")

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

    if wl.results.revision:
        revision = wl.results.revision
        click.echo(f"Revision result: {revision.get('operation', '?')}")
        if revision.get("input_atom_id"):
            click.echo(f"Input atom: {revision['input_atom_id']}")
        target_atom_ids = revision.get("target_atom_ids") or []
        if target_atom_ids:
            click.echo(f"Target atoms: {', '.join(target_atom_ids)}")
        if revision.get("error"):
            click.echo(f"Revision error: {revision['error']}")
        result_payload = revision.get("result") or {}
        rejected = result_payload.get("rejected_atom_ids") or []
        if rejected:
            click.echo(f"Rejected atoms: {', '.join(rejected)}")
        accepted = result_payload.get("accepted_atom_ids") or []
        if accepted:
            click.echo(f"Accepted atoms: {', '.join(accepted)}")

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
    # Delegate to run with default reasoning options
    ctx = click.get_current_context()
    ctx.invoke(
        worldline_run, name=name, bindings=(), overrides=(), targets=(),
        strategy=None, context=None,
        reasoning_backend="claim_graph", semantics="grounded",
        set_comparison="elitist", link_principle="last", decision_criterion="pignistic",
        pessimism_index=0.5, praf_strategy="auto", praf_epsilon=0.01,
        praf_confidence=0.95, praf_seed=None,
        revision_operation=None, revision_atom=None, revision_target=None,
        revision_conflicts=(), revision_operator=None,
    )


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

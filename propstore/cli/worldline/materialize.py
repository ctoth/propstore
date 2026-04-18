"""Worldline create, run, and refresh CLI commands."""
from __future__ import annotations

import sys

import click

from propstore.artifacts.refs import WorldlineRef
from propstore.cli.helpers import open_world_model
from propstore.cli.worldline import (
    _apply_reasoning_options,
    _apply_revision_options,
    _build_policy_dict,
    _build_revision_dict,
    _load_worldline_definition,
    _parse_kv_args,
    worldline,
)
from propstore.repository import Repository


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
    ref = WorldlineRef(name)
    address = repo.families.worldlines.family.address_for(repo, ref)
    if repo.families.worldlines.load(ref) is not None:
        click.echo(
            f"ERROR: Worldline '{name}' already exists at {address.require_path()}",
            err=True,
        )
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

    repo.families.worldlines.save(
        ref,
        wl.to_document(),
        message=f"Create worldline: {name}",
    )
    repo.snapshot.sync_worktree()

    click.echo(f"Created worldline '{name}' at {address.require_path()}")


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
    """Run (materialize) a worldline, loading its saved definition if present.

    If a worldline file with NAME already exists, this command loads it and
    materializes it as-is — all CLI options (--bind, --with, --target,
    --strategy, --context, reasoning flags, revision flags) are ignored in
    that case. CLI options are only consulted when NAME does not yet exist,
    in which case they are used to construct and persist a fresh definition
    before the first materialization.
    """
    from propstore.worldline import WorldlineDefinition, run_worldline

    repo: Repository = obj["repo"]

    # If file exists, load it; otherwise create from CLI args
    ref = WorldlineRef(name)
    if repo.families.worldlines.load(ref) is not None:
        wl = _load_worldline_definition(repo, name)
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

    with open_world_model(repo) as wm:
        result = run_worldline(wl, wm)
    wl.results = result

    repo.families.worldlines.save(
        ref,
        wl.to_document(),
        message=f"Materialize worldline: {name}",
    )
    repo.snapshot.sync_worktree()

    click.echo(f"Worldline '{name}' materialized ({len(result.values)} targets)")
    for target, val in result.values.items():
        status = val.status
        value = val.value
        source = val.source or ""
        if value is not None:
            click.echo(f"  {target}: {value} ({status}, {source})")
        else:
            reason = val.reason or ""
            click.echo(f"  {target}: {status} — {reason}")


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


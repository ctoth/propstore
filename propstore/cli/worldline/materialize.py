"""Worldline create, run, and refresh CLI commands."""
from __future__ import annotations

import sys

import click

from propstore.cli.output import emit

from propstore.app.worldlines import (
    WorldlineAlreadyExistsError,
    WorldlineCreateRequest,
    WorldlinePolicyOptions,
    WorldlineRevisionOptions,
    WorldlineRunRequest,
    WorldlineValidationError,
    create_worldline as run_create_worldline,
    materialize_worldline,
    parse_worldline_revision_atom,
)
from propstore.cli.worldline import (
    _apply_reasoning_options,
    _apply_revision_options,
    _parse_kv_args,
    worldline,
)
from propstore.repository import Repository


def _parse_revision_conflicts(raw_conflicts: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    conflicts: dict[str, tuple[str, ...]] = {}
    for entry in raw_conflicts:
        atom_id, sep, targets = entry.partition("=")
        if not sep:
            raise click.ClickException(
                "Invalid --revision-conflict; expected atom_id=target[,target...]",
            )
        parsed_targets = tuple(
            target.strip()
            for target in targets.split(",")
            if target.strip()
        )
        conflicts[str(atom_id)] = parsed_targets
    return conflicts


def _policy_options(
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
) -> WorldlinePolicyOptions:
    return WorldlinePolicyOptions(
        strategy=strategy,
        reasoning_backend=reasoning_backend,
        semantics=semantics,
        set_comparison=set_comparison,
        link_principle=link_principle,
        decision_criterion=decision_criterion,
        pessimism_index=pessimism_index,
        praf_strategy=praf_strategy,
        praf_epsilon=praf_epsilon,
        praf_confidence=praf_confidence,
        praf_seed=praf_seed,
    )


def _revision_options(
    revision_operation: str | None,
    revision_atom: str | None,
    revision_target: str | None,
    revision_conflicts: tuple[str, ...],
    revision_operator: str | None,
) -> WorldlineRevisionOptions:
    return WorldlineRevisionOptions(
        operation=revision_operation,
        atom=parse_worldline_revision_atom(revision_atom),
        target=revision_target,
        conflicts=_parse_revision_conflicts(revision_conflicts),
        operator=revision_operator,
    )


def _coerce_override_values(overrides: tuple[str, ...]) -> dict[str, float | str]:
    override_dict: dict[str, float | str] = {}
    for key, value in _parse_kv_args(overrides).items():
        if isinstance(value, bool):
            override_dict[key] = str(value)
            continue
        if isinstance(value, int | float):
            override_dict[key] = float(value)
            continue
        if isinstance(value, str):
            try:
                override_dict[key] = float(value)
            except ValueError:
                override_dict[key] = value
            continue
        override_dict[key] = str(value)
    return override_dict


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
    repo: Repository = obj["repo"]
    try:
        report = run_create_worldline(
            repo,
            WorldlineCreateRequest(
                name=name,
                bindings=_parse_kv_args(bindings),
                overrides=_coerce_override_values(overrides),
                targets=tuple(targets),
                context_id=context,
                policy=_policy_options(
                    strategy,
                    reasoning_backend,
                    semantics,
                    set_comparison,
                    link_principle,
                    decision_criterion,
                    pessimism_index,
                    praf_strategy,
                    praf_epsilon,
                    praf_confidence,
                    praf_seed,
                ),
                revision=_revision_options(
                    revision_operation,
                    revision_atom,
                    revision_target,
                    revision_conflicts,
                    revision_operator,
                ),
            ),
        )
    except WorldlineAlreadyExistsError as exc:
        emit(f"ERROR: {exc}", err=True)
        sys.exit(1)
    except WorldlineValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    emit(f"Created worldline '{report.name}' at {report.path}")


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
    repo: Repository = obj["repo"]
    try:
        report = materialize_worldline(
            repo,
            WorldlineRunRequest(
                name=name,
                bindings=_parse_kv_args(bindings),
                overrides=_coerce_override_values(overrides),
                targets=tuple(targets),
                context_id=context,
                policy=_policy_options(
                    strategy,
                    reasoning_backend,
                    semantics,
                    set_comparison,
                    link_principle,
                    decision_criterion,
                    pessimism_index,
                    praf_strategy,
                    praf_epsilon,
                    praf_confidence,
                    praf_seed,
                ),
                revision=_revision_options(
                    revision_operation,
                    revision_atom,
                    revision_target,
                    revision_conflicts,
                    revision_operator,
                ),
            ),
        )
    except WorldlineValidationError as exc:
        emit(f"ERROR: {exc}", err=True)
        sys.exit(1)

    result = report.result
    emit(f"Worldline '{name}' materialized ({len(result.values)} targets)")
    for target, val in result.values.items():
        status = val.status
        value = val.value
        source = val.source or ""
        if value is not None:
            emit(f"  {target}: {value} ({status}, {source})")
        else:
            reason = val.reason or ""
            emit(f"  {target}: {status} — {reason}")


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


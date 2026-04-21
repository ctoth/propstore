"""Revision-oriented ``pks world`` command adapters."""
from __future__ import annotations

import json

import click

from propstore.cli.output import emit, emit_section, emit_table

from propstore.app.world_revision import (
    AppIteratedReviseRequest,
    AppRevisionContractRequest,
    AppRevisionExpandRequest,
    AppRevisionExplainRequest,
    AppRevisionReviseRequest,
    AppRevisionWorldRequest,
    RevisionAtomDisplay,
    WorldRevisionValidationError,
    revision_atom_display,
    world_revision_base as run_world_revision_base,
    world_revision_contract as run_world_revision_contract,
    world_revision_entrenchment as run_world_revision_entrenchment,
    world_revision_epistemic_state as run_world_revision_epistemic_state,
    world_revision_expand as run_world_revision_expand,
    world_revision_explain as run_world_revision_explain,
    world_revision_iterated_revise as run_world_revision_iterated_revise,
    world_revision_revise as run_world_revision_revise,
)
from propstore.cli.world import (
    _format_assumption_ids,
    parse_world_binding_args,
    world,
)
from propstore.repository import Repository


@world.group("revision", no_args_is_help=True)
def revision() -> None:
    """Inspect and run scoped revision operations."""


def _format_revision_payload(payload: RevisionAtomDisplay) -> str:
    parts: list[str] = []
    if payload.claim_type:
        parts.append(f"type={payload.claim_type}")
    if payload.concept_id:
        parts.append(f"concept={payload.concept_id}")
    if payload.value is not None:
        if payload.unit:
            parts.append(f"value={payload.value} {payload.unit}")
        else:
            parts.append(f"value={payload.value}")
    return " ".join(parts)


def _format_revision_assumption(assumption) -> str:
    return (
        f"{assumption.assumption_id}: kind={assumption.kind} "
        f"source={assumption.source} cel={assumption.cel}"
    )


def _parse_revision_atom_json(atom_json: str) -> dict:
    try:
        data = json.loads(atom_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --atom JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise click.ClickException("--atom must decode to a JSON object")
    return data


def _emit_revision_result(result) -> None:
    emit_section(f"Accepted ({len(result.accepted_atom_ids)} atoms):", result.accepted_atom_ids)
    emit_section(f"Rejected ({len(result.rejected_atom_ids)} atoms):", result.rejected_atom_ids)
    emit(f"Incision set: {', '.join(result.incision_set) if result.incision_set else '(none)'}")


def _emit_revision_explanation(explanation) -> None:
    emit(f"Accepted ({len(explanation.accepted_atom_ids)} atoms):")
    for atom_id in explanation.accepted_atom_ids:
        emit(f"  {atom_id}")

    emit(f"Rejected ({len(explanation.rejected_atom_ids)} atoms):")
    for atom_id in explanation.rejected_atom_ids:
        emit(f"  {atom_id}")

    incision = explanation.incision_set
    emit(f"Incision set: {', '.join(incision) if incision else '(none)'}")
    emit("Atoms:")
    for atom_id, detail in explanation.atoms.items():
        line = f"  {atom_id}: status={detail.status} reason={detail.reason}"
        ranking = detail.ranking
        if ranking is not None:
            line += f" support_count={ranking.support_count or 0}"
        emit(line)


def _emit_epistemic_state(state) -> None:
    emit(f"Iterated state ({len(state.accepted_atom_ids)} accepted atoms)")
    emit(f"History length: {len(state.history)}")
    emit_section(
        "Ranking:",
        (f"{rank}. {atom_id}" for rank, atom_id in enumerate(state.ranked_atom_ids, start=1)),
    )


def _emit_iterated_revision(result, previous_state, next_state, *, operator: str) -> None:
    emit(f"Operator: {operator}")
    _emit_revision_result(result)
    emit(f"Next state ({len(next_state.accepted_atom_ids)} accepted atoms)")
    emit(f"History length: {len(next_state.history)}")
    emit_section(
        "Ranking:",
        (f"{rank}. {atom_id}" for rank, atom_id in enumerate(next_state.ranked_atom_ids, start=1)),
    )
    emit("Ranking delta:")
    previous_ranking = previous_state.ranking
    for atom_id in next_state.ranked_atom_ids:
        old_rank = previous_ranking.get(atom_id)
        new_rank = next_state.ranking.get(atom_id)
        if old_rank is None:
            emit(f"  + {atom_id}: new at rank {new_rank}")
        elif old_rank != new_rank:
            emit(f"  ~ {atom_id}: {old_rank} -> {new_rank}")
    for atom_id, old_rank in previous_ranking.items():
        if atom_id not in next_state.ranking:
            emit(f"  - {atom_id}: dropped from rank {old_rank}")
    emit("History:")
    last_episode = next_state.history[-1] if next_state.history else None
    if last_episode is None:
        emit("  (empty)")
    else:
        emit(
            f"  {last_episode.operator}: input={last_episode.input_atom_id} "
            f"targets={list(last_episode.target_atom_ids)} "
            f"accepted={len(last_episode.accepted_atom_ids)} "
            f"rejected={len(last_episode.rejected_atom_ids)}"
        )


@revision.command("base")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision base")
@click.pass_obj
def world_revision_base(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show the current revision-facing belief base for a scoped world."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    base = run_world_revision_base(
        repo,
        AppRevisionWorldRequest(bindings=bindings, context=context),
    )

    emit(f"Revision base ({len(base.atoms)} atoms, {len(base.assumptions)} assumptions)")
    for atom in base.atoms:
        display = revision_atom_display(atom)
        details = _format_revision_payload(display)
        if details:
            emit(f"  {display.display_id}: {details}")
        else:
            emit(f"  {display.display_id}")

    if base.assumptions:
        emit_section(
            "Assumptions:",
            (_format_revision_assumption(assumption) for assumption in base.assumptions),
        )


@revision.command("entrenchment")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision entrenchment")
@click.pass_obj
def world_revision_entrenchment(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show the current deterministic entrenchment ordering for a scoped world."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = run_world_revision_entrenchment(
        repo,
        AppRevisionWorldRequest(bindings=bindings, context=context),
    )

    emit(f"Entrenchment ({len(report.ranked_atom_ids)} atoms)")
    rows: list[tuple[int, str, int, str, object]] = []
    for rank, atom_id in enumerate(report.ranked_atom_ids, start=1):
        reason = report.reasons.get(atom_id)
        support_count = 0 if reason is None or reason.support_count is None else reason.support_count
        essential_support = () if reason is None else reason.essential_support
        override = None if reason is None else reason.override_priority
        rows.append(
            (
                rank,
                atom_id,
                support_count,
                _format_assumption_ids(essential_support),
                override,
            )
        )
    emit_table(("Rank", "Atom", "Support", "Essential support", "Override"), rows, indent="  ")


@revision.command("expand")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to add")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_expand(obj: dict, args: tuple[str, ...], atom_json: str, context: str | None) -> None:
    """Expand the scoped revision belief base without mutating source YAML."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    result = run_world_revision_expand(
        repo,
        AppRevisionExpandRequest(
            world=AppRevisionWorldRequest(bindings=bindings, context=context),
            atom=_parse_revision_atom_json(atom_json),
        ),
    )
    _emit_revision_result(result)


@revision.command("contract")
@click.argument("args", nargs=-1)
@click.option("--target", "targets", multiple=True, required=True, help="Existing atom or claim id to contract")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_contract(obj: dict, args: tuple[str, ...], targets: tuple[str, ...], context: str | None) -> None:
    """Contract the scoped revision belief base without mutating source YAML."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    result = run_world_revision_contract(
        repo,
        AppRevisionContractRequest(
            world=AppRevisionWorldRequest(bindings=bindings, context=context),
            targets=targets,
        ),
    )
    _emit_revision_result(result)


@revision.command("revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_revise(
    obj: dict,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Revise the scoped belief base without mutating source YAML."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    result = run_world_revision_revise(
        repo,
        AppRevisionReviseRequest(
            world=AppRevisionWorldRequest(bindings=bindings, context=context),
            atom=_parse_revision_atom_json(atom_json),
            conflicts=conflicts,
        ),
    )
    _emit_revision_result(result)


@revision.command("explain")
@click.argument("args", nargs=-1)
@click.option("--operation", type=click.Choice(["expand", "contract", "revise"]), required=True)
@click.option("--atom", "atom_json", default=None, help="JSON revision atom for expand/revise")
@click.option("--target", "targets", multiple=True, help="Existing atom or claim id for contract")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_revision_explain(
    obj: dict,
    args: tuple[str, ...],
    operation: str,
    atom_json: str | None,
    targets: tuple[str, ...],
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Explain one revision operation over the current scoped world."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    atom = None if atom_json is None else _parse_revision_atom_json(atom_json)
    try:
        explanation = run_world_revision_explain(
            repo,
            AppRevisionExplainRequest(
                world=AppRevisionWorldRequest(bindings=bindings, context=context),
                operation=operation,
                atom=atom,
                targets=targets,
                conflicts=conflicts,
            ),
        )
    except WorldRevisionValidationError as exc:
        raise click.ClickException(str(exc)) from exc
    _emit_revision_explanation(explanation)


@revision.command("iterated-state")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the iterated revision state")
@click.pass_obj
def world_iterated_state(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Inspect the current explicit iterated revision state for a scoped world."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    state = run_world_revision_epistemic_state(
        repo,
        AppRevisionWorldRequest(bindings=bindings, context=context),
    )
    _emit_epistemic_state(state)


@revision.command("iterated-revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--operator", type=click.Choice(["restrained", "lexicographic"]), default="restrained")
@click.option("--context", default=None, help="Context to scope the iterated revision operation")
@click.pass_obj
def world_iterated_revise(
    obj: dict,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    operator: str,
    context: str | None,
) -> None:
    """Run one iterated revision episode and print the next explicit state."""
    repo: Repository = obj["repo"]
    bindings, _ = parse_world_binding_args(args)
    report = run_world_revision_iterated_revise(
        repo,
        AppIteratedReviseRequest(
            world=AppRevisionWorldRequest(bindings=bindings, context=context),
            atom=_parse_revision_atom_json(atom_json),
            conflicts=conflicts,
            operator=operator,
        ),
    )
    _emit_iterated_revision(
        report.result,
        report.previous_state,
        report.next_state,
        operator=report.operator,
    )

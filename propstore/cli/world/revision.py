"""Revision-oriented ``pks world`` command adapters."""
from __future__ import annotations

import json
from collections.abc import Mapping

import click

from propstore.app.world import open_app_world_model, parse_world_binding_args
from propstore.cli.world import (
    _format_assumption_ids,
    world,
)
from propstore.repository import Repository


@world.group("revision", no_args_is_help=True)
def revision() -> None:
    """Inspect and run scoped revision operations."""


def _format_revision_payload(payload: dict) -> str:
    claim_type = payload.get("type")
    concept_id = payload.get("concept_id")
    value = payload.get("value")
    unit = payload.get("unit")
    parts: list[str] = []
    if claim_type:
        parts.append(f"type={claim_type}")
    if concept_id:
        parts.append(f"concept={concept_id}")
    if value is not None:
        if unit:
            parts.append(f"value={value} {unit}")
        else:
            parts.append(f"value={value}")
    return " ".join(parts)


def _revision_atom_display_id(atom_id: str, *, payload: Mapping[str, object] | None = None) -> str:
    if payload is not None:
        logical_id = payload.get("logical_id") or payload.get("primary_logical_id")
        if isinstance(logical_id, str) and logical_id:
            return f"claim:{logical_id.split(':', 1)[1] if ':' in logical_id else logical_id}"
        logical_ids = payload.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if not isinstance(entry, Mapping):
                    continue
                value = entry.get("value")
                if isinstance(value, str) and value:
                    return f"claim:{value}"
    return atom_id


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
    click.echo(f"Accepted ({len(result.accepted_atom_ids)} atoms):")
    for atom_id in result.accepted_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Rejected ({len(result.rejected_atom_ids)} atoms):")
    for atom_id in result.rejected_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Incision set: {', '.join(result.incision_set) if result.incision_set else '(none)'}")


def _emit_revision_explanation(explanation) -> None:
    click.echo(f"Accepted ({len(explanation.accepted_atom_ids)} atoms):")
    for atom_id in explanation.accepted_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Rejected ({len(explanation.rejected_atom_ids)} atoms):")
    for atom_id in explanation.rejected_atom_ids:
        click.echo(f"  {atom_id}")

    incision = explanation.incision_set
    click.echo(f"Incision set: {', '.join(incision) if incision else '(none)'}")
    click.echo("Atoms:")
    for atom_id, detail in explanation.atoms.items():
        line = f"  {atom_id}: status={detail.status} reason={detail.reason}"
        ranking = detail.ranking
        if ranking is not None:
            line += f" support_count={ranking.support_count or 0}"
        click.echo(line)


def _emit_epistemic_state(state) -> None:
    click.echo(f"Iterated state ({len(state.accepted_atom_ids)} accepted atoms)")
    click.echo(f"History length: {len(state.history)}")
    click.echo("Ranking:")
    for rank, atom_id in enumerate(state.ranked_atom_ids, start=1):
        click.echo(f"  {rank}. {atom_id}")


def _emit_iterated_revision(result, previous_state, next_state, *, operator: str) -> None:
    click.echo(f"Operator: {operator}")
    _emit_revision_result(result)
    click.echo(f"Next state ({len(next_state.accepted_atom_ids)} accepted atoms)")
    click.echo(f"History length: {len(next_state.history)}")
    click.echo("Ranking:")
    for rank, atom_id in enumerate(next_state.ranked_atom_ids, start=1):
        click.echo(f"  {rank}. {atom_id}")
    click.echo("Ranking delta:")
    previous_ranking = previous_state.ranking
    for atom_id in next_state.ranked_atom_ids:
        old_rank = previous_ranking.get(atom_id)
        new_rank = next_state.ranking.get(atom_id)
        if old_rank is None:
            click.echo(f"  + {atom_id}: new at rank {new_rank}")
        elif old_rank != new_rank:
            click.echo(f"  ~ {atom_id}: {old_rank} -> {new_rank}")
    for atom_id, old_rank in previous_ranking.items():
        if atom_id not in next_state.ranking:
            click.echo(f"  - {atom_id}: dropped from rank {old_rank}")
    click.echo("History:")
    last_episode = next_state.history[-1] if next_state.history else None
    if last_episode is None:
        click.echo("  (empty)")
    else:
        click.echo(
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
    from propstore.support_revision.state import is_assumption_atom, is_claim_atom
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revision_base,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        base = revision_base(wm, RevisionWorldRequest(bindings, context))

        click.echo(f"Revision base ({len(base.atoms)} atoms, {len(base.assumptions)} assumptions)")
        for atom in base.atoms:
            if is_claim_atom(atom):
                payload = atom.claim.to_dict()
            elif is_assumption_atom(atom):
                payload = {
                    "assumption_id": atom.assumption.assumption_id,
                    "cel": atom.assumption.cel,
                    "kind": atom.assumption.kind,
                    "source": atom.assumption.source,
                }
            else:
                raise TypeError(f"unsupported revision atom: {type(atom).__name__}")
            details = _format_revision_payload(payload)
            atom_display_id = _revision_atom_display_id(atom.atom_id, payload=payload)
            if details:
                click.echo(f"  {atom_display_id}: {details}")
            else:
                click.echo(f"  {atom_display_id}")

        if base.assumptions:
            click.echo("Assumptions:")
            for assumption in base.assumptions:
                click.echo(f"  {_format_revision_assumption(assumption)}")


@revision.command("entrenchment")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision entrenchment")
@click.pass_obj
def world_revision_entrenchment(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show the current deterministic entrenchment ordering for a scoped world."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revision_entrenchment,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = revision_entrenchment(wm, RevisionWorldRequest(bindings, context))

        click.echo(f"Entrenchment ({len(report.ranked_atom_ids)} atoms)")
        for rank, atom_id in enumerate(report.ranked_atom_ids, start=1):
            reason = report.reasons.get(atom_id)
            support_count = 0 if reason is None or reason.support_count is None else reason.support_count
            essential_support = () if reason is None else reason.essential_support
            override = None if reason is None else reason.override_priority
            click.echo(
                f"  {rank}. {atom_id} "
                f"support_count={support_count} "
                f"essential_support={_format_assumption_ids(essential_support)} "
                f"override={override}"
            )


@revision.command("expand")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to add")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_expand(obj: dict, args: tuple[str, ...], atom_json: str, context: str | None) -> None:
    """Expand the scoped revision belief base without mutating source YAML."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        expand_revision,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        result = expand_revision(
            wm,
            RevisionWorldRequest(bindings, context),
            _parse_revision_atom_json(atom_json),
        )
        _emit_revision_result(result)


@revision.command("contract")
@click.argument("args", nargs=-1)
@click.option("--target", "targets", multiple=True, required=True, help="Existing atom or claim id to contract")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_contract(obj: dict, args: tuple[str, ...], targets: tuple[str, ...], context: str | None) -> None:
    """Contract the scoped revision belief base without mutating source YAML."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        contract_revision,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        result = contract_revision(
            wm,
            RevisionWorldRequest(bindings, context),
            targets,
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
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revise_world,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        result = revise_world(
            wm,
            RevisionWorldRequest(bindings, context),
            _parse_revision_atom_json(atom_json),
            conflicts,
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
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        explain_revision_operation,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)

        if operation == "expand":
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation expand")
            atom = _parse_revision_atom_json(atom_json)
        elif operation == "contract":
            if not targets:
                raise click.ClickException("--target is required for --operation contract")
            atom = None
        else:
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation revise")
            atom = _parse_revision_atom_json(atom_json)

        try:
            explanation = explain_revision_operation(
                wm,
                RevisionWorldRequest(bindings, context),
                operation=operation,
                atom=atom,
                targets=targets,
                conflicts=conflicts,
            )
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        _emit_revision_explanation(explanation)


@revision.command("iterated-state")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the iterated revision state")
@click.pass_obj
def world_iterated_state(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Inspect the current explicit iterated revision state for a scoped world."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        epistemic_state,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        state = epistemic_state(wm, RevisionWorldRequest(bindings, context))
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
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        iterated_revise_world,
    )

    repo: Repository = obj["repo"]
    with open_app_world_model(repo) as wm:
        bindings, _ = parse_world_binding_args(args)
        report = iterated_revise_world(
            wm,
            RevisionWorldRequest(bindings, context),
            atom=_parse_revision_atom_json(atom_json),
            conflicts=conflicts,
            operator=operator,
        )
        _emit_iterated_revision(
            report.result,
            report.previous_state,
            report.next_state,
            operator=report.operator,
        )

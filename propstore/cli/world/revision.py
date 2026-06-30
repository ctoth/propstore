"""Revision-oriented ``pks world`` command adapters.

``world revision base|entrenchment|expand|contract|revise|explain|iterated-state
|iterated-revise`` over the :mod:`propstore.support_revision.workflows` owner
tier. The workflow functions take a :class:`~propstore.core.environment.WorldStore`
(a :class:`~propstore.world.WorldQuery` is one) and a
:class:`~propstore.support_revision.workflows.RevisionWorldRequest`; this adapter
only parses flags, calls them, and renders the typed results.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import click

from propstore.cli.helpers import CliContext, fail
from propstore.cli.output import emit, emit_section, emit_table
from propstore.cli.world import (
    format_assumption_ids,
    is_json_object,
    open_world,
    parse_world_binding_args,
    world,
    world_repo,
)
from propstore.support_revision.belief_set_adapter import (
    DEFAULT_ITERATED_OPERATOR,
    LEXICOGRAPHIC_OPERATOR,
    RESTRAINED_OPERATOR,
)
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import RevisionExplanation
from propstore.support_revision.state import (
    BeliefBase,
    EpistemicState,
    RevisionResult,
)
from propstore.support_revision.workflows import (
    IteratedRevisionReport,
    RevisionWorldRequest,
    contract_revision,
    epistemic_state,
    expand_revision,
    explain_revision_operation,
    iterated_revise_world,
    revise_world,
    revision_base,
    revision_entrenchment,
)


@world.group("revision", no_args_is_help=True)
def revision() -> None:
    """Inspect and run scoped revision operations."""


def _request(args: tuple[str, ...], context: str | None) -> RevisionWorldRequest:
    bindings, _ = parse_world_binding_args(args)
    return RevisionWorldRequest(bindings=bindings, context_id=context)


def _parse_atom_json(atom_json: str) -> Mapping[str, Any]:
    try:
        data = json.loads(atom_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"invalid --atom JSON: {exc}") from exc
    if not is_json_object(data):
        raise click.ClickException("--atom must decode to a JSON object")
    return data


# ── inspect ────────────────────────────────────────────────────────────────────


@revision.command("base")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision base.")
@click.pass_obj
def world_revision_base(
    obj: CliContext, args: tuple[str, ...], context: str | None
) -> None:
    """Show the current revision-facing belief base for a scoped world."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        base: BeliefBase = revision_base(world_query, _request(args, context))

    emit(
        f"Revision base ({len(base.atoms)} atoms, "
        f"{len(base.assumptions)} assumptions)"
    )
    for atom in base.atoms:
        emit(f"  {atom.atom_id}")
    if base.assumptions:
        emit_section(
            "Assumptions:",
            (
                f"{assumption.assumption_id}: kind={assumption.kind} "
                f"source={assumption.source} cel={assumption.cel}"
                for assumption in base.assumptions
            ),
        )


@revision.command("entrenchment")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the entrenchment.")
@click.pass_obj
def world_revision_entrenchment(
    obj: CliContext, args: tuple[str, ...], context: str | None
) -> None:
    """Show the deterministic entrenchment ordering for a scoped world."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        report: EntrenchmentReport = revision_entrenchment(
            world_query, _request(args, context)
        )

    emit(f"Entrenchment ({len(report.ranked_atom_ids)} atoms)")
    rows: list[tuple[object, ...]] = []
    for rank, atom_id in enumerate(report.ranked_atom_ids, start=1):
        reason = report.reasons.get(atom_id)
        support_count = (
            0 if reason is None or reason.support_count is None else reason.support_count
        )
        essential = () if reason is None else reason.essential_support
        override = None if reason is None else reason.override_priority
        rows.append(
            (
                rank,
                atom_id,
                support_count,
                format_assumption_ids([str(value) for value in essential]),
                override,
            )
        )
    emit_table(
        ("Rank", "Atom", "Support", "Essential support", "Override"),
        rows,
        indent="  ",
    )


@revision.command("iterated-state")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the iterated state.")
@click.pass_obj
def world_iterated_state(
    obj: CliContext, args: tuple[str, ...], context: str | None
) -> None:
    """Inspect the current explicit iterated revision state for a scoped world."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        state: EpistemicState = epistemic_state(world_query, _request(args, context))
    _emit_epistemic_state(state)


# ── operations ──────────────────────────────────────────────────────────────────


@revision.command("expand")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to add.")
@click.option("--context", default=None, help="Context to scope the operation.")
@click.pass_obj
def world_expand(
    obj: CliContext, args: tuple[str, ...], atom_json: str, context: str | None
) -> None:
    """Expand the scoped revision belief base without mutating source YAML."""

    repo = world_repo(obj)
    atom = _parse_atom_json(atom_json)
    with open_world(repo) as world_query:
        result = expand_revision(world_query, _request(args, context), atom)
    _emit_revision_result(result)


@revision.command("contract")
@click.argument("args", nargs=-1)
@click.option(
    "--target",
    "targets",
    multiple=True,
    required=True,
    help="Existing atom or claim id to contract.",
)
@click.option("--context", default=None, help="Context to scope the operation.")
@click.pass_obj
def world_contract(
    obj: CliContext,
    args: tuple[str, ...],
    targets: tuple[str, ...],
    context: str | None,
) -> None:
    """Contract the scoped revision belief base without mutating source YAML."""

    repo = world_repo(obj)
    with open_world(repo) as world_query:
        result = contract_revision(world_query, _request(args, context), targets)
    _emit_revision_result(result)


@revision.command("revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit.")
@click.option(
    "--conflict",
    "conflicts",
    multiple=True,
    help="Existing atom or claim id that conflicts with the new atom.",
)
@click.option("--context", default=None, help="Context to scope the operation.")
@click.pass_obj
def world_revise(
    obj: CliContext,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Revise the scoped belief base without mutating source YAML."""

    repo = world_repo(obj)
    atom = _parse_atom_json(atom_json)
    with open_world(repo) as world_query:
        result = revise_world(world_query, _request(args, context), atom, conflicts)
    _emit_revision_result(result)


@revision.command("explain")
@click.argument("args", nargs=-1)
@click.option(
    "--operation",
    type=click.Choice(["expand", "contract", "revise"]),
    required=True,
)
@click.option("--atom", "atom_json", default=None, help="JSON atom for expand/revise.")
@click.option(
    "--target", "targets", multiple=True, help="Atom or claim id for contract."
)
@click.option(
    "--conflict", "conflicts", multiple=True, help="Conflicting atom or claim id."
)
@click.option("--context", default=None, help="Context to scope the operation.")
@click.pass_obj
def world_revision_explain(
    obj: CliContext,
    args: tuple[str, ...],
    operation: str,
    atom_json: str | None,
    targets: tuple[str, ...],
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Explain one revision operation over the current scoped world."""

    repo = world_repo(obj)
    atom = None if atom_json is None else _parse_atom_json(atom_json)
    with open_world(repo) as world_query:
        try:
            explanation = explain_revision_operation(
                world_query,
                _request(args, context),
                operation=operation,
                atom=atom,
                targets=targets,
                conflicts=conflicts,
            )
        except ValueError as exc:
            fail(str(exc))
    _emit_revision_explanation(explanation)


@revision.command("iterated-revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit.")
@click.option(
    "--conflict", "conflicts", multiple=True, help="Conflicting atom or claim id."
)
@click.option(
    "--operator",
    type=click.Choice([RESTRAINED_OPERATOR, LEXICOGRAPHIC_OPERATOR]),
    default=DEFAULT_ITERATED_OPERATOR,
)
@click.option("--context", default=None, help="Context to scope the operation.")
@click.pass_obj
def world_iterated_revise(
    obj: CliContext,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    operator: str,
    context: str | None,
) -> None:
    """Run one iterated revision episode and print the next explicit state."""

    repo = world_repo(obj)
    atom = _parse_atom_json(atom_json)
    with open_world(repo) as world_query:
        report: IteratedRevisionReport = iterated_revise_world(
            world_query,
            _request(args, context),
            atom=atom,
            conflicts=conflicts,
            operator=operator,
        )
    _emit_iterated_revision(report)


# ── rendering helpers ───────────────────────────────────────────────────────────


def _emit_revision_result(result: RevisionResult) -> None:
    decision = result.decision
    if decision is not None:
        emit("Formal decision:")
        emit(f"  operation: {decision.operation}")
        emit(f"  policy: {decision.policy}")
        emit_section(
            f"  accepted formulas ({len(decision.accepted_formula_ids)}):",
            decision.accepted_formula_ids,
        )
        emit_section(
            f"  rejected formulas ({len(decision.rejected_formula_ids)}):",
            decision.rejected_formula_ids,
        )

    realization = result.realization
    accepted = (
        result.accepted_atom_ids
        if realization is None
        else realization.accepted_atom_ids
    )
    rejected = (
        result.rejected_atom_ids
        if realization is None
        else realization.rejected_atom_ids
    )
    incision = result.incision_set if realization is None else realization.incision_set
    emit("Support realization:")
    emit_section(f"Accepted ({len(accepted)} atoms):", accepted)
    emit_section(f"Rejected ({len(rejected)} atoms):", rejected)
    emit(f"Incision set: {', '.join(incision) if incision else '(none)'}")


def _emit_revision_explanation(explanation: RevisionExplanation) -> None:
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


def _emit_epistemic_state(state: EpistemicState) -> None:
    emit(f"Iterated state ({len(state.accepted_atom_ids)} accepted atoms)")
    emit(f"History length: {len(state.history)}")
    emit_section(
        "Ranking:",
        (
            f"{rank}. {atom_id}"
            for rank, atom_id in enumerate(state.ranked_atom_ids, start=1)
        ),
    )


def _emit_iterated_revision(report: IteratedRevisionReport) -> None:
    next_state = report.next_state
    previous_state = report.previous_state
    emit(f"Operator: {report.operator}")
    _emit_revision_result(report.result)
    emit(f"Next state ({len(next_state.accepted_atom_ids)} accepted atoms)")
    emit(f"History length: {len(next_state.history)}")
    emit_section(
        "Ranking:",
        (
            f"{rank}. {atom_id}"
            for rank, atom_id in enumerate(next_state.ranked_atom_ids, start=1)
        ),
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

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.explanation_types import EntrenchmentReason
from propstore.support_revision.operators import normalize_revision_input, revise
from propstore.support_revision.state import BeliefBase, EpistemicState, RevisionEpisode, RevisionResult


def make_epistemic_state(
    base: BeliefBase,
    entrenchment: EntrenchmentReport,
) -> EpistemicState:
    """Create an explicit epistemic state from a stabilized belief base."""
    return EpistemicState(
        scope=base.scope,
        base=base,
        accepted_atom_ids=tuple(atom.atom_id for atom in base.atoms),
        ranked_atom_ids=tuple(entrenchment.ranked_atom_ids),
        ranking={atom_id: idx for idx, atom_id in enumerate(entrenchment.ranked_atom_ids)},
        entrenchment_reasons=dict(entrenchment.reasons),
        history=(),
    )


def advance_epistemic_state(
    state: EpistemicState,
    result: RevisionResult,
    entrenchment: EntrenchmentReport,
    *,
    operator: str,
    input_atom_id: str | None = None,
    target_atom_ids: tuple[str, ...] = (),
) -> EpistemicState:
    """Advance one revision episode from an old epistemic state to a new one."""
    episode = RevisionEpisode(
        operator=operator,
        input_atom_id=input_atom_id,
        target_atom_ids=tuple(target_atom_ids),
        accepted_atom_ids=tuple(result.accepted_atom_ids),
        rejected_atom_ids=tuple(result.rejected_atom_ids),
        incision_set=tuple(result.incision_set),
        explanation=dict(result.explanation),
    )
    return EpistemicState(
        scope=result.revised_base.scope,
        base=result.revised_base,
        accepted_atom_ids=tuple(result.accepted_atom_ids),
        ranked_atom_ids=tuple(entrenchment.ranked_atom_ids),
        ranking={atom_id: idx for idx, atom_id in enumerate(entrenchment.ranked_atom_ids)},
        entrenchment_reasons=dict(entrenchment.reasons),
        history=state.history + (episode,),
    )


def iterated_revise(
    state: EpistemicState,
    atom,
    *,
    max_candidates: int,
    conflicts: dict[str, tuple[str, ...] | list[str]] | None = None,
    operator: str = "restrained",
) -> tuple[RevisionResult, EpistemicState]:
    """Revise an explicit epistemic state using a selected iterated operator family."""
    if len(state.scope.merge_parent_commits) > 1:
        raise ValueError("iterated revision is undefined at a merge point; use an explicit merge path")

    normalized = normalize_revision_input(state.base, atom)
    current_entrenchment = _entrenchment_from_state(state)
    if conflicts is None:
        conflict_items = ()
    elif isinstance(conflicts, Mapping):
        conflict_items = conflicts.items()
    else:
        raise ValueError("iterated revision conflicts must be a mapping")
    conflict_map = {atom_id: tuple(targets) for atom_id, targets in conflict_items}
    result = revise(
        state.base,
        normalized,
        entrenchment=current_entrenchment,
        max_candidates=max_candidates,
        conflicts=conflict_map or None,
    )
    next_entrenchment = _updated_entrenchment_report(
        state,
        result,
        input_atom_id=normalized.atom_id,
        operator=operator,
    )
    next_state = advance_epistemic_state(
        state,
        result,
        next_entrenchment,
        operator=operator,
        input_atom_id=normalized.atom_id,
        target_atom_ids=tuple(conflict_map.get(normalized.atom_id, ())),
    )
    return result, next_state


def epistemic_state_payload(state: EpistemicState) -> dict:
    """Return a JSON-friendly payload for persistence or replay tooling."""
    from propstore.support_revision.history import EpistemicSnapshot

    return EpistemicSnapshot.from_state(state).to_dict()


def _entrenchment_from_state(state: EpistemicState) -> EntrenchmentReport:
    return EntrenchmentReport(
        ranked_atom_ids=tuple(state.ranked_atom_ids),
        reasons=dict(state.entrenchment_reasons),
    )


def _updated_entrenchment_report(
    state: EpistemicState,
    result: RevisionResult,
    *,
    input_atom_id: str,
    operator: str,
) -> EntrenchmentReport:
    accepted_set = set(result.accepted_atom_ids)
    survivor_order = [
        atom_id
        for atom_id in state.ranked_atom_ids
        if atom_id in accepted_set and atom_id != input_atom_id
    ]
    extras = [
        atom_id
        for atom_id in result.accepted_atom_ids
        if atom_id not in survivor_order and atom_id != input_atom_id
    ]

    if operator == "lexicographic":
        ranked_atom_ids = (
            (input_atom_id,) if input_atom_id in accepted_set else ()
        ) + tuple(survivor_order) + tuple(extras)
    elif operator == "restrained":
        ranked_atom_ids = tuple(survivor_order) + (
            (input_atom_id,) if input_atom_id in accepted_set else ()
        ) + tuple(extras)
    else:
        raise ValueError(f"Unsupported iterated revision operator: {operator}")

    reasons = {
        atom_id: state.entrenchment_reasons.get(atom_id, EntrenchmentReason())
        for atom_id in ranked_atom_ids
    }
    if input_atom_id in accepted_set:
        reasons[input_atom_id] = replace(
            reasons.get(input_atom_id, EntrenchmentReason()),
            iterated_operator=operator,
            revised_in=True,
        )

    return EntrenchmentReport(
        ranked_atom_ids=ranked_atom_ids,
        reasons=reasons,
    )

from __future__ import annotations

from collections.abc import Mapping

from propstore.support_revision.entrenchment import EntrenchmentReport, compute_entrenchment
from propstore.support_revision.belief_set_adapter import (
    DEFAULT_ITERATED_OPERATOR,
    decide_iterated_revise,
)
from propstore.support_revision.input_normalization import normalize_revision_input
from propstore.support_revision.realization import realize_formal_decision
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
    operator: str = DEFAULT_ITERATED_OPERATOR,
) -> tuple[RevisionResult, EpistemicState]:
    """Revise an explicit epistemic state using a selected iterated operator family."""
    if len(state.scope.merge_parent_commits) > 1:
        raise ValueError("iterated revision is undefined at a merge point; use an explicit merge path")

    normalized = normalize_revision_input(state.base, atom)
    current_entrenchment = compute_entrenchment(None, state.base)
    if conflicts is None:
        conflict_items = ()
    elif isinstance(conflicts, Mapping):
        conflict_items = conflicts.items()
    else:
        raise ValueError("iterated revision conflicts must be a mapping")
    conflict_map = {atom_id: tuple(targets) for atom_id, targets in conflict_items}
    formal_decision = decide_iterated_revise(
        state.base,
        normalized,
        conflicts=tuple(conflict_map.get(normalized.atom_id, ())),
        operator=operator,
        max_alphabet_size=16,
    )
    result = realize_formal_decision(
        state.base,
        formal_decision,
        extra_atoms=(normalized,),
        accepted_reason="revised_in",
        rejected_reason="revised_out",
        support_entrenchment=current_entrenchment,
        max_candidates=max_candidates,
    )
    next_entrenchment = compute_entrenchment(None, result.revised_base)
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

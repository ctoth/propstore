from __future__ import annotations

from dataclasses import asdict

from propstore.revision.entrenchment import EntrenchmentReport
from propstore.revision.state import BeliefBase, EpistemicState, RevisionEpisode, RevisionResult


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
        entrenchment_reasons={atom_id: dict(reason) for atom_id, reason in entrenchment.reasons.items()},
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
        explanation={atom_id: dict(detail) for atom_id, detail in result.explanation.items()},
    )
    return EpistemicState(
        scope=result.revised_base.scope,
        base=result.revised_base,
        accepted_atom_ids=tuple(result.accepted_atom_ids),
        ranked_atom_ids=tuple(entrenchment.ranked_atom_ids),
        entrenchment_reasons={atom_id: dict(reason) for atom_id, reason in entrenchment.reasons.items()},
        history=state.history + (episode,),
    )


def epistemic_state_payload(state: EpistemicState) -> dict:
    """Return a JSON-friendly payload for persistence or replay tooling."""
    payload = asdict(state)
    payload["accepted_atom_ids"] = list(state.accepted_atom_ids)
    payload["ranked_atom_ids"] = list(state.ranked_atom_ids)
    payload["history"] = [
        {
            **episode_payload,
            "target_atom_ids": list(episode.target_atom_ids),
            "accepted_atom_ids": list(episode.accepted_atom_ids),
            "rejected_atom_ids": list(episode.rejected_atom_ids),
            "incision_set": list(episode.incision_set),
        }
        for episode, episode_payload in zip(state.history, payload["history"], strict=False)
    ]
    return payload

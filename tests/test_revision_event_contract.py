from __future__ import annotations

import pytest

from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.history import EpistemicSnapshot, JournalOperator
from propstore.support_revision.iterated import advance_epistemic_state, make_epistemic_state
from propstore.support_revision.snapshot_types import EpistemicStateSnapshot
from propstore.support_revision.state import RevisionRealizationFailure
from propstore.support_revision.dispatch import dispatch
from tests.support_revision.formal_realization_helpers import contract_via_formal_decision
from tests.test_revision_operators import _base_with_shared_support


_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


def test_revision_episode_carries_typed_event_contract() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract_via_formal_decision(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id for atom_id in entrenchment.ranked_atom_ids if atom_id in result.accepted_atom_ids
        ),
        reasons=dict(entrenchment.reasons),
    )

    next_state = advance_epistemic_state(
        state,
        result,
        next_entrenchment,
        operator="contract",
        target_atom_ids=(ids["legacy"],),
        policy_snapshot=_POLICY,
        replay_status="direct",
    )

    event = next_state.history[-1].event
    assert event is not None
    assert event.pre_state_hash == EpistemicSnapshot.from_state(state).content_hash
    assert event.operation == "contract"
    assert event.input_atom_id is None
    assert event.target_atom_ids == (ids["legacy"],)
    assert event.decision == result.decision
    assert event.realization == result.realization
    assert event.policy_snapshot == _POLICY
    assert event.replay_status == "direct"
    assert event.realization_failure is None


def test_revision_event_survives_epistemic_state_snapshot_roundtrip() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    result = contract_via_formal_decision(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )
    next_entrenchment = EntrenchmentReport(
        ranked_atom_ids=tuple(
            atom_id for atom_id in entrenchment.ranked_atom_ids if atom_id in result.accepted_atom_ids
        ),
        reasons=dict(entrenchment.reasons),
    )
    next_state = advance_epistemic_state(
        state,
        result,
        next_entrenchment,
        operator="contract",
        target_atom_ids=(ids["legacy"],),
        policy_snapshot=_POLICY,
        replay_status="direct",
    )

    payload = EpistemicStateSnapshot.from_state(next_state).to_dict()
    restored = EpistemicStateSnapshot.from_mapping(payload).to_state()

    assert payload["history"][0]["event"]["decision"]["operation"] == "contract"
    assert restored.history[-1].event == next_state.history[-1].event


def test_dispatch_exposes_formal_decision_when_realization_fails() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)

    with pytest.raises(RevisionRealizationFailure) as exc_info:
        dispatch(
            JournalOperator.CONTRACT,
            state_in=state.to_canonical_dict(),
            operator_input={
                "targets": (ids["legacy"],),
                "max_candidates": 0,
            },
            policy=_POLICY,
        )

    event = exc_info.value.event
    assert event.pre_state_hash == EpistemicSnapshot.from_state(state).content_hash
    assert event.operation == "contract"
    assert event.target_atom_ids == (ids["legacy"],)
    assert event.decision is not None
    assert event.decision.operation == "contract"
    assert event.realization is None
    assert event.policy_snapshot == _POLICY
    assert event.replay_status == "realization_failed"
    assert "exact enumeration exceeded" in event.realization_failure

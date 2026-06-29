from __future__ import annotations

from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.state import (
    FormalRevisionDecisionReport,
    RevisionEvent,
    SupportRevisionRealization,
)
from propstore.worldline.definition import WorldlineRevisionQuery
from propstore.worldline.revision_capture import capture_journal
from tests.fixtures.journal import direct_dispatch, make_assertion_atom, make_state
from tests.test_capture_journal import _JournalBound


_POLICY = {
    "revision_policy_version": "revision.v1",
    "ranking_policy_version": "ranking.v1",
    "entrenchment_policy_version": "entrenchment.v1",
}


def _event() -> RevisionEvent:
    return RevisionEvent(
        operation="revise",
        pre_state_hash="state:before",
        input_atom_id="atom:new",
        target_atom_ids=("atom:old",),
        decision=FormalRevisionDecisionReport(
            operation="revise",
            policy="belief_set.agm.revise",
            input_formula_ids=("atom:new", "not:atom:old"),
            accepted_formula_ids=("atom:new",),
            rejected_formula_ids=("atom:old",),
            epistemic_state_hash="formal:state",
            trace={"ranking_provenance": {"status": "defaulted"}},
        ),
        realization=SupportRevisionRealization(
            accepted_atom_ids=("atom:new",),
            rejected_atom_ids=("atom:old",),
            incision_set=("assumption:weak",),
        ),
        policy_snapshot=_POLICY,
        replay_status="replayed",
    )


def test_revision_event_content_hash_changes_for_decision_realization_and_policy() -> None:
    event = _event()

    changed_decision = replace(event, decision=replace(event.decision, policy="belief_set.agm.contract"))
    changed_realization = replace(
        event,
        realization=replace(event.realization, accepted_atom_ids=("atom:other",)),
    )
    changed_policy = replace(
        event,
        policy_snapshot={
            "revision_policy_version": "revision.v1",
            "ranking_policy_version": "ranking.v2",
            "entrenchment_policy_version": "entrenchment.v1",
        },
    )

    assert event.content_hash != changed_decision.content_hash
    assert event.content_hash != changed_realization.content_hash
    assert event.content_hash != changed_policy.content_hash


@settings(max_examples=12)
@pytest.mark.property
@given(order=st.permutations(tuple(_POLICY.items())))
def test_revision_event_content_hash_is_stable_under_policy_mapping_order(
    order: tuple[tuple[str, str], ...],
) -> None:
    assert _event().content_hash == replace(_event(), policy_snapshot=dict(order)).content_hash


@settings(max_examples=8, deadline=None)
@pytest.mark.property
@given(count=st.integers(min_value=1, max_value=3))
def test_generated_revise_journals_replay_and_events_keep_disjoint_realization_sets(
    count: int,
) -> None:
    atoms = tuple(
        make_assertion_atom(
            relation_local=f"wl_prop_rel_{index}",
            subject=f"wl_prop_subject_{index}",
            value=f"wl_prop_value_{index}",
            source_claim_local_ids=(f"wl_prop_claim_{index}",),
        )
        for index in range(count)
    )
    state = make_state(atoms=atoms, accepted_atom_ids=())
    queries = tuple(_revise_query(atom.atom_id) for atom in atoms)

    journal = capture_journal(_JournalBound(state), queries)
    replay = journal.replay()
    direct = direct_dispatch(journal, len(journal.entries) - 1)

    assert replay.ok
    assert journal.entries[-1].normalized_state_out == direct.to_canonical_dict()
    for entry in journal.entries:
        event = entry.state_out.state.history[-1].event
        assert event is not None
        assert event.realization is not None
        assert set(event.realization.accepted_atom_ids).isdisjoint(event.realization.rejected_atom_ids)


def _revise_query(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "revise",
        "atom": {"kind": "assertion", "id": atom_id},
        "conflicts": {},
    })
    assert query is not None
    return query

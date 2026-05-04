from __future__ import annotations

from dataclasses import dataclass

import pytest
from hypothesis import given
from hypothesis import strategies as st

from propstore.support_revision.history import TransitionJournal
from propstore.support_revision.state import EpistemicState
from propstore.worldline.definition import WorldlineRevisionQuery
from tests.fixtures.journal import (
    direct_dispatch,
    make_assertion_atom,
    make_state,
)


@dataclass(frozen=True)
class _JournalBound:
    initial_state: EpistemicState

    def epistemic_state(self) -> EpistemicState:
        return self.initial_state


def _query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "revise",
        "atom": {"kind": "assertion", "id": atom_id},
        "conflicts": {},
    })
    assert query is not None
    return query


@st.composite
def _journal_inputs(draw):
    count = draw(st.integers(min_value=1, max_value=5))
    atoms = tuple(
        make_assertion_atom(
            relation_local=f"capture_rel_{index}",
            subject=f"capture_subject_{index}",
            value=f"capture_value_{index}",
            source_claim_local_ids=(f"capture_claim_{index}",),
        )
        for index in range(count)
    )
    initial_state = make_state(atoms=atoms, accepted_atom_ids=())
    queries = tuple(_query_for(atom.atom_id) for atom in atoms)
    return _JournalBound(initial_state), queries


@pytest.mark.property
@given(data=_journal_inputs())
def test_p_cap_1_capture_journal_is_deterministic(data) -> None:
    from propstore.worldline.revision_capture import capture_journal

    bound, queries = data

    first = capture_journal(bound, queries)
    second = capture_journal(bound, queries)

    assert isinstance(first, TransitionJournal)
    assert first == second
    assert tuple(entry.content_hash for entry in first.entries) == tuple(
        entry.content_hash for entry in second.entries
    )


@pytest.mark.property
@given(data=_journal_inputs())
def test_p_cap_2_capture_replay_matches_direct_dispatch(data) -> None:
    from propstore.worldline.revision_capture import capture_journal

    bound, queries = data

    journal = capture_journal(bound, queries)
    replayed = journal.replay()
    direct = direct_dispatch(journal, len(journal.entries) - 1)

    assert replayed.ok
    assert not replayed.errors
    assert not replayed.divergences
    assert journal.entries[-1].normalized_state_out == direct.to_canonical_dict()

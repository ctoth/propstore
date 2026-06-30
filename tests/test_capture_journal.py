"""Worldline journal-capture tests.

Only the in-memory ``capture_journal`` surface is exercised here. The
document-codec / CLI / ``at_journal_step`` cases from the reference suite ride on
Phase-8/9 surfaces (``families.documents.worldlines``, ``cli.worldline.journal``,
``Repository``-backed ``WorldStore``) that the rewrite has not landed yet; they
remain listed in ``docs/rewrite/deferred-tests.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.support_revision.history import JournalOperator, TransitionJournal
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


class _JournalWorld:
    def __init__(self, bound: _JournalBound) -> None:
        self._bound = bound

    def bind(self, environment=None, *, policy=None, **conditions):
        return self._bound


def _query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "revise",
        "atom": {"kind": "assertion", "id": atom_id},
        "conflicts": {},
    })
    assert query is not None
    return query


def _contract_query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "contract",
        "target": atom_id,
    })
    assert query is not None
    return query


def _expand_query_for(atom_id: str) -> WorldlineRevisionQuery:
    query = WorldlineRevisionQuery.from_dict({
        "operation": "expand",
        "atom": {"kind": "assertion", "id": atom_id},
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
@settings(deadline=None)
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


def test_phase2_acceptance_captures_revise_revise_contract_journal() -> None:
    from propstore.worldline.revision_capture import capture_journal

    first = make_assertion_atom(
        relation_local="rrc_rel_1",
        subject="rrc_subject_1",
        value="rrc_value_1",
        source_claim_local_ids=("rrc_claim_1",),
    )
    second = make_assertion_atom(
        relation_local="rrc_rel_2",
        subject="rrc_subject_2",
        value="rrc_value_2",
        source_claim_local_ids=("rrc_claim_2",),
    )
    initial_state = make_state(atoms=(first, second), accepted_atom_ids=())

    journal = capture_journal(
        _JournalBound(initial_state),
        (
            _query_for(first.atom_id),
            _query_for(second.atom_id),
            _contract_query_for(first.atom_id),
        ),
    )
    direct = direct_dispatch(journal, 2)

    assert len(journal.entries) == 3
    assert [entry.operation.name for entry in journal.entries] == [
        "revise",
        "revise",
        "contract",
    ]
    assert journal.check_chain_integrity().ok
    assert journal.replay().ok
    assert journal.entries[-1].normalized_state_out == direct.to_canonical_dict()
    assert first.atom_id not in journal.entries[-1].state_out.state.accepted_atom_ids


def test_capture_journal_preserves_expand_as_expand_operator() -> None:
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="expand_rel",
        subject="expand_subject",
        value="expand_value",
        source_claim_local_ids=("expand_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())

    journal = capture_journal(
        _JournalBound(initial_state),
        (_expand_query_for(atom.atom_id),),
    )

    assert len(journal.entries) == 1
    assert journal.entries[0].operation.name == "expand"
    assert journal.entries[0].operator is JournalOperator.EXPAND
    assert journal.replay().ok
    assert atom.atom_id in journal.entries[0].state_out.state.accepted_atom_ids

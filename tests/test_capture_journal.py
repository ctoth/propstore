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


def test_p_cap_3_legacy_worldline_definition_roundtrips_without_journal() -> None:
    from propstore.worldline import WorldlineDefinition

    definition = WorldlineDefinition.from_dict({
        "id": "legacy_without_journal",
        "targets": ["target"],
    })

    document = definition.to_document()
    loaded = WorldlineDefinition.from_document(document)

    assert loaded.journal is None
    assert "journal" not in loaded.to_dict()


def test_p_cap_4_journal_bearing_worldline_definition_roundtrips() -> None:
    from propstore.worldline import WorldlineDefinition
    from propstore.worldline.revision_capture import capture_journal

    atom = make_assertion_atom(
        relation_local="document_rel",
        subject="document_subject",
        value="document_value",
        source_claim_local_ids=("document_claim",),
    )
    initial_state = make_state(atoms=(atom,), accepted_atom_ids=())
    query = _query_for(atom.atom_id)
    journal = capture_journal(_JournalBound(initial_state), (query,))

    definition = WorldlineDefinition.from_dict({
        "id": "journal_bearing",
        "targets": ["target"],
        "journal": journal.to_dict(),
    })

    document = definition.to_document()
    loaded = WorldlineDefinition.from_document(document)

    assert loaded.journal is not None
    assert loaded.journal == journal
    assert loaded.to_dict()["journal"] == journal.to_dict()

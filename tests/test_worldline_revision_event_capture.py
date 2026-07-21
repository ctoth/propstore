from __future__ import annotations

from dataclasses import dataclass

from quire.documents import convert_document_value

from propstore.reporting import json_ready
from propstore.support_revision.explanation_types import RevisionExplanation
from propstore.support_revision.history import EpistemicSnapshot
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.state import EpistemicState, RevisionResult
from propstore.worldline.query import WorldlineRevisionQuery
from propstore.worldline.revision_capture import capture_revision_state
from propstore.worldline.revision_types import (
    RevisionAtomRef,
    RevisionConflictSelection,
    WorldlineRevisionState,
)
from tests.support_revision.formal_realization_helpers import revise_via_formal_decision
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support


@dataclass(frozen=True)
class _CaptureBound:
    state: EpistemicState
    result: RevisionResult

    def epistemic_state(self) -> EpistemicState:
        return self.state

    def revise(self, atom, *, conflicts, max_candidates):
        return self.result

    def revision_explain(self, result):
        return RevisionExplanation(
            accepted_atom_ids=tuple(result.accepted_atom_ids),
            rejected_atom_ids=tuple(result.rejected_atom_ids),
        )


def test_capture_revision_state_serializes_revision_event_contract() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    initial_state = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("worldline_event_new")
    result = revise_via_formal_decision(
        base,
        new_atom,
        entrenchment=entrenchment,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
    )
    query = WorldlineRevisionQuery(
        operation="revise",
        atom=RevisionAtomRef(kind="assertion", assertion_id=new_atom.atom_id),
        conflicts=RevisionConflictSelection(
            targets_by_atom_id={new_atom.atom_id: (ids["legacy"],)}
        ),
    )

    captured = capture_revision_state(_CaptureBound(initial_state, result), query)
    # The charter stores this state typed; Quire owns the round trip.
    payload = json_ready(captured)
    restored = convert_document_value(
        payload, WorldlineRevisionState, source="worldline"
    )

    assert captured.event is not None
    assert (
        captured.event.pre_state_hash
        == EpistemicSnapshot.from_state(initial_state).content_hash
    )
    assert captured.event.operation == "revise"
    assert captured.event.input_atom_id == new_atom.atom_id
    assert captured.event.target_atom_ids == (ids["legacy"],)
    assert captured.event.decision == result.decision
    assert captured.event.realization == result.realization
    assert payload["event"]["decision"]["operation"] == "revise"
    assert restored is not None
    assert restored.event == captured.event

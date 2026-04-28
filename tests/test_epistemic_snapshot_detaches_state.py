"""WS-J Step 8/J-M2: epistemic snapshots detach from live state objects."""

from __future__ import annotations

from propstore.support_revision.snapshot_types import EpistemicStateSnapshot
from propstore.support_revision.iterated import make_epistemic_state
from tests.test_revision_operators import _base_with_shared_support


def test_ws_j_epistemic_state_snapshot_from_state_deep_copies_payload() -> None:
    base, entrenchment, _ = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)

    snapshot = EpistemicStateSnapshot.from_state(state)

    assert tuple(atom.atom_id for atom in snapshot.base.atoms) == tuple(
        atom.atom_id for atom in state.base.atoms
    )
    assert snapshot.base.support_sets == state.base.support_sets
    assert snapshot.base.essential_support == state.base.essential_support
    assert snapshot.base is not state.base
    assert snapshot.scope == state.scope
    assert snapshot.scope is not state.scope
    assert snapshot.ranking == state.ranking
    assert snapshot.ranking is not state.ranking
    assert snapshot.entrenchment_reasons == state.entrenchment_reasons
    assert snapshot.entrenchment_reasons is not state.entrenchment_reasons

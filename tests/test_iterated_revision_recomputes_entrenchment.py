"""WS-J Step 6: iterated revision recomputes entrenchment from the current base."""

from __future__ import annotations

from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_ws_j_iterated_revision_uses_current_base_entrenchment_not_stale_state_ranking() -> None:
    base, _, stale_right_first, ids = _history_sensitive_base()
    state = make_epistemic_state(base, stale_right_first)
    new_atom = make_assertion_atom("fresh_entrenchment")

    result, _ = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
        operator="restrained",
    )

    assert result.incision_set == ("assumption:right_path",)

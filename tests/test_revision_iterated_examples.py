"""Named examples for support-state ranking updates."""

from __future__ import annotations

from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_restrained_example_keeps_prior_priority_path_when_admitting_new_assertion() -> None:
    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new = make_assertion_atom("new")

    _, next_state = iterated_revise(
        state,
        new,
        max_candidates=8,
        conflicts={new.atom_id: (ids["legacy"],)},
        operator="restrained",
    )

    assert ids["left_dependent"] in next_state.accepted_atom_ids
    assert ids["right_dependent"] not in next_state.accepted_atom_ids
    assert next_state.ranked_atom_ids[-1] == new.atom_id


def test_lexicographic_example_promotes_new_assertion_to_top_priority() -> None:
    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new = make_assertion_atom("new")

    _, next_state = iterated_revise(
        state,
        new,
        max_candidates=8,
        conflicts={new.atom_id: (ids["legacy"],)},
        operator="lexicographic",
    )

    assert next_state.ranked_atom_ids[0] == new.atom_id
    assert ids["left_dependent"] in next_state.accepted_atom_ids

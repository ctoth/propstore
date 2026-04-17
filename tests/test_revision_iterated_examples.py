"""Named examples for support-state ranking updates."""

from __future__ import annotations

from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.test_revision_iterated import _history_sensitive_base


def test_restrained_example_keeps_prior_priority_path_when_admitting_new_claim() -> None:
    base, entrenchment, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)

    _, next_state = iterated_revise(
        state,
        {"kind": "claim", "id": "new"},
        conflicts={"claim:new": ("claim:legacy",)},
        operator="restrained",
    )

    assert "claim:left_dependent" in next_state.accepted_atom_ids
    assert "claim:right_dependent" not in next_state.accepted_atom_ids
    assert next_state.ranked_atom_ids[-1] == "claim:new"


def test_lexicographic_example_promotes_new_claim_to_top_priority() -> None:
    base, entrenchment, _ = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)

    _, next_state = iterated_revise(
        state,
        {"kind": "claim", "id": "new"},
        conflicts={"claim:new": ("claim:legacy",)},
        operator="lexicographic",
    )

    assert next_state.ranked_atom_ids[0] == "claim:new"
    assert "claim:left_dependent" in next_state.accepted_atom_ids

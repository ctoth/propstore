"""Named examples for support-state ranking updates."""

from __future__ import annotations

from propstore.support_revision.entrenchment import compute_entrenchment
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_restrained_example_reports_formal_policy_and_recomputed_ranking() -> None:
    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new = make_assertion_atom("new")

    result, next_state = iterated_revise(
        state,
        new,
        max_candidates=8,
        conflicts={new.atom_id: (ids["legacy"],)},
        operator="restrained",
    )

    assert result.decision is not None
    assert result.realization is not None
    assert result.decision.policy == "belief_set.iterated.restrained"
    assert result.realization.accepted_atom_ids == result.accepted_atom_ids
    assert ids["left_dependent"] in next_state.accepted_atom_ids
    assert ids["right_dependent"] not in next_state.accepted_atom_ids
    assert next_state.ranked_atom_ids == compute_entrenchment(None, result.revised_base).ranked_atom_ids


def test_lexicographic_example_reports_formal_policy_and_recomputed_ranking() -> None:
    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new = make_assertion_atom("new")

    result, next_state = iterated_revise(
        state,
        new,
        max_candidates=8,
        conflicts={new.atom_id: (ids["legacy"],)},
        operator="lexicographic",
    )

    assert result.decision is not None
    assert result.realization is not None
    assert result.decision.policy == "belief_set.iterated.lexicographic"
    assert result.realization.accepted_atom_ids == result.accepted_atom_ids
    assert ids["left_dependent"] in next_state.accepted_atom_ids
    assert next_state.ranked_atom_ids == compute_entrenchment(None, result.revised_base).ranked_atom_ids

from __future__ import annotations

from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base


def test_iterated_revision_uses_adapter_formal_decision_and_support_realization() -> None:
    base, entrenchment, _, ids = _history_sensitive_base()
    state = make_epistemic_state(base, entrenchment)
    new_atom = make_assertion_atom("new")

    result, next_state = iterated_revise(
        state,
        new_atom,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
        operator="restrained",
    )

    assert result.decision is not None
    assert result.realization is not None
    assert result.decision.operation == "iterated_revise"
    assert result.decision.policy == "belief_set.iterated.restrained"
    assert result.decision.epistemic_state_hash is not None
    assert result.realization.accepted_atom_ids == result.accepted_atom_ids
    assert next_state.history[-1].accepted_atom_ids == result.accepted_atom_ids

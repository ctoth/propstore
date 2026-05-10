from __future__ import annotations

from propstore.support_revision.belief_dynamics import (
    contract_belief_base,
    expand_belief_base,
    revise_belief_base,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support


def test_expand_contract_revise_return_split_decision_and_realization() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    new_atom = make_assertion_atom("new")

    expanded = expand_belief_base(base, new_atom)
    contracted = contract_belief_base(base, (ids["legacy"],), entrenchment=entrenchment, max_candidates=8)
    revised = revise_belief_base(
        base,
        new_atom,
        entrenchment=entrenchment,
        max_candidates=8,
        conflicts={new_atom.atom_id: (ids["legacy"],)},
    )

    assert expanded.decision is not None
    assert expanded.realization is not None
    assert expanded.decision.operation == "expand"
    assert expanded.realization.accepted_atom_ids == expanded.accepted_atom_ids

    assert contracted.decision is not None
    assert contracted.realization is not None
    assert contracted.decision.operation == "contract"
    assert contracted.incision_set == ("assumption:shared_weak",)
    assert contracted.realization.incision_set == contracted.incision_set

    assert revised.decision is not None
    assert revised.realization is not None
    assert revised.decision.operation == "revise"
    assert new_atom.atom_id in revised.accepted_atom_ids
    assert ids["legacy"] in revised.rejected_atom_ids
    assert revised.realization.rejected_atom_ids == revised.rejected_atom_ids

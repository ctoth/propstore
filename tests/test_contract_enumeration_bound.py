"""WS-J Step 5: public support-revision operators require enumeration budgets."""

from __future__ import annotations

import pytest

from propstore.core.anytime import EnumerationExceeded
from propstore.support_revision.belief_dynamics import contract_belief_base, revise_belief_base
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support


def test_contract_requires_explicit_max_candidates() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    with pytest.raises(TypeError, match="max_candidates"):
        contract_belief_base(base, (ids["legacy"],), entrenchment=entrenchment)


def test_contract_raises_enumeration_exceeded_at_caller_budget() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    with pytest.raises(EnumerationExceeded) as exc_info:
        contract_belief_base(
            base,
            (ids["legacy"],),
            entrenchment=entrenchment,
            max_candidates=0,
        )

    assert exc_info.value.partial_count == 0
    assert exc_info.value.max_candidates == 0


def test_contract_completes_with_sufficient_caller_budget() -> None:
    base, entrenchment, ids = _base_with_shared_support()

    result = contract_belief_base(
        base,
        (ids["legacy"],),
        entrenchment=entrenchment,
        max_candidates=8,
    )

    assert result.incision_set == ("assumption:shared_weak",)


def test_revise_requires_explicit_max_candidates() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    atom = make_assertion_atom("bounded_revise")

    with pytest.raises(TypeError, match="max_candidates"):
        revise_belief_base(
            base,
            atom,
            entrenchment=entrenchment,
            conflicts={atom.atom_id: (ids["legacy"],)},
        )


def test_iterated_revise_requires_explicit_max_candidates() -> None:
    base, entrenchment, ids = _base_with_shared_support()
    state = make_epistemic_state(base, entrenchment)
    atom = make_assertion_atom("bounded_iterated")

    with pytest.raises(TypeError, match="max_candidates"):
        iterated_revise(
            state,
            atom,
            conflicts={atom.atom_id: (ids["legacy"],)},
            operator="restrained",
        )

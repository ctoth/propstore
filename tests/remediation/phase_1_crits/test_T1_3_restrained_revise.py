from __future__ import annotations

import pytest
from hypothesis import given, settings

from propstore.belief_set import Atom, SpohnEpistemicState
from propstore.belief_set.core import BeliefSet
from propstore.belief_set.iterated import restrained_revise
from tests.test_belief_set_iterated_postulates import st_formula, st_state


P = Atom("p")
ALPHABET = frozenset({"p", "q"})
P_AND_NOT_Q = frozenset({"p"})
NOT_P_AND_NOT_Q = frozenset()
P_AND_Q = frozenset({"p", "q"})
NOT_P_AND_Q = frozenset({"q"})


def test_restrained_revision_splits_only_equal_nonminimal_preorder_levels() -> None:
    """Booth-Meyer 2006 (RR): old strict order survives outside minimal alpha-worlds."""
    state = SpohnEpistemicState.from_ranks(
        ALPHABET,
        {
            P_AND_NOT_Q: 0,
            NOT_P_AND_NOT_Q: 0,
            P_AND_Q: 1,
            NOT_P_AND_Q: 1,
        },
    )

    revised = restrained_revise(state, P).state

    assert revised.ranks[NOT_P_AND_NOT_Q] < revised.ranks[P_AND_Q]


@pytest.mark.property
@given(state=st_state(), formula=st_formula)
@settings(deadline=None)
def test_restrained_revision_satisfies_booth_meyer_rr_pairwise_condition(
    state: SpohnEpistemicState,
    formula,
) -> None:
    """Booth-Meyer 2006 (RR): non-minimal revised worlds obey the restrained preorder."""
    if not BeliefSet.from_formula(state.alphabet, formula).is_consistent:
        return

    revised = restrained_revise(state, formula).state
    minimal_revised_worlds = revised.belief_set.models

    for left in revised.ranks:
        for right in revised.ranks:
            if left in minimal_revised_worlds or right in minimal_revised_worlds:
                continue

            old_left_rank = state.ranks[left]
            old_right_rank = state.ranks[right]
            expected_left_not_worse = (
                old_left_rank < old_right_rank
                or (
                    old_left_rank <= old_right_rank
                    and (formula.evaluate(left) or not formula.evaluate(right))
                )
            )
            actual_left_not_worse = revised.ranks[left] <= revised.ranks[right]

            assert actual_left_not_worse is expected_left_not_worse

from __future__ import annotations

import math

from propstore.belief_set import BOTTOM, Atom, BeliefSet, SpohnEpistemicState, revise


def test_revise_by_inconsistent_formula_returns_inconsistent_theory() -> None:
    """Class A - must fail today: agm.py short-circuits K*2 for bottom."""

    p = Atom("p")
    alphabet = frozenset({"p"})
    state = SpohnEpistemicState.from_ranks(
        alphabet,
        {
            frozenset({"p"}): 0,
            frozenset(): 1,
        },
    )

    result = revise(state, BOTTOM)

    assert result.belief_set == BeliefSet.contradiction(alphabet)
    assert result.state.belief_set == BeliefSet.contradiction(alphabet)
    assert all(math.isinf(rank) for rank in result.state.ranks.values())
    assert result.trace.pre_image_fingerprint == state.belief_set.fingerprint()
    assert state.belief_set.entails(p)

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.belief_set import Atom, Formula, SpohnEpistemicState, conjunction, negate
from propstore.belief_set.core import BeliefSet
from propstore.belief_set.iterated import lexicographic_revise, restrained_revise


pytestmark = pytest.mark.property

ALPHABET = frozenset({"p", "q", "r"})
P = Atom("p")
Q = Atom("q")
R = Atom("r")
FORMULAS: tuple[Formula, ...] = (
    P,
    Q,
    R,
    negate(P),
    negate(Q),
    conjunction(P, Q),
    conjunction(P, negate(Q)),
)
st_formula = st.sampled_from(FORMULAS)


@st.composite
def st_state(draw) -> SpohnEpistemicState:
    return SpohnEpistemicState.from_ranks(
        ALPHABET,
        {
            world: draw(st.integers(min_value=0, max_value=5))
            for world in BeliefSet.all_worlds(ALPHABET)
        },
    )


@given(st_state(), st_formula)
@settings(deadline=None)
def test_nayak_spohn_lexicographic_revision_places_all_input_worlds_first(
    state: SpohnEpistemicState,
    formula: Formula,
) -> None:
    assume(BeliefSet.from_formula(ALPHABET, formula).is_consistent)

    revised = lexicographic_revise(state, formula).state
    formula_worlds = [world for world in revised.ranks if formula.evaluate(world)]
    counter_worlds = [world for world in revised.ranks if not formula.evaluate(world)]

    assert revised.belief_set.entails(formula)
    assert max(revised.ranks[world] for world in formula_worlds) < min(
        revised.ranks[world] for world in counter_worlds
    )
    for left in formula_worlds:
        for right in formula_worlds:
            assert (state.ranks[left] <= state.ranks[right]) == (
                revised.ranks[left] <= revised.ranks[right]
            )


@given(st_state(), st_formula)
@settings(deadline=None)
def test_booth_meyer_2006_restrained_revision_preserves_internal_preorders(
    state: SpohnEpistemicState,
    formula: Formula,
) -> None:
    assume(BeliefSet.from_formula(ALPHABET, formula).is_consistent)

    revised = restrained_revise(state, formula).state
    assert revised.belief_set.entails(formula)

    for expected_truth in (True, False):
        worlds = [world for world in revised.ranks if formula.evaluate(world) is expected_truth]
        for left in worlds:
            for right in worlds:
                assert (state.ranks[left] <= state.ranks[right]) == (
                    revised.ranks[left] <= revised.ranks[right]
                )


@given(st_state(), st_formula, st_formula)
@settings(deadline=None)
def test_booth_meyer_2006_restrained_revision_satisfies_admissibility_p(
    state: SpohnEpistemicState,
    mu: Formula,
    alpha: Formula,
) -> None:
    assume(BeliefSet.from_formula(ALPHABET, mu).is_consistent)
    assume(BeliefSet.from_formula(ALPHABET, alpha).is_consistent)
    assume(not BeliefSet.from_formula(ALPHABET, alpha).entails(negate(mu)))

    after_mu_then_alpha = restrained_revise(restrained_revise(state, mu).state, alpha).belief_set
    after_alpha = restrained_revise(state, alpha).belief_set

    if after_alpha.entails(alpha):
        assert after_mu_then_alpha.entails(alpha)

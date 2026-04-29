from __future__ import annotations

import pytest

from propstore.belief_set import Atom, BeliefSet, SpohnEpistemicState, conjunction, revise
from propstore.core.anytime import EnumerationExceeded


def test_revise_rejects_signature_larger_than_configured_alphabet_budget() -> None:
    """Class B - coverage gate for bounded finite-world enumeration."""

    state = SpohnEpistemicState.from_belief_set(BeliefSet.tautology(frozenset({"p", "q"})))
    formula = conjunction(Atom("p"), Atom("q"), Atom("r"))

    with pytest.raises(EnumerationExceeded):
        revise(state, formula, max_alphabet_size=2)


def test_revise_default_budget_rejects_twenty_one_atom_signature() -> None:
    """Class B - coverage gate for the default WS-G 16-atom budget."""

    base = frozenset({"p", "q", "r"})
    state = SpohnEpistemicState.from_belief_set(BeliefSet.tautology(base))
    formula = conjunction(*(Atom(f"x{index}") for index in range(18)))

    with pytest.raises(EnumerationExceeded):
        revise(state, formula)

from __future__ import annotations

from dataclasses import dataclass

from propstore.belief_set.agm import SpohnEpistemicState
from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import Formula, negate


@dataclass(frozen=True, slots=True)
class EpistemicEntrenchment:
    """Gärdenfors-Makinson style entrenchment induced by a Spohn ranking."""

    state: SpohnEpistemicState

    @classmethod
    def from_state(cls, state: SpohnEpistemicState) -> EpistemicEntrenchment:
        return cls(state=state)

    def leq(self, left: Formula, right: Formula) -> bool:
        """Return whether ``left`` is no more entrenched than ``right``."""
        return self._negation_rank(left) <= self._negation_rank(right)

    def _negation_rank(self, formula: Formula) -> float:
        signature = self.state.alphabet | formula.atoms()
        state = self.state
        if signature != state.alphabet:
            from propstore.belief_set.agm import _extend_state

            state = _extend_state(state, signature)
        countermodels = [
            world
            for world in BeliefSet.all_worlds(signature)
            if negate(formula).evaluate(world)
        ]
        if not countermodels:
            return float("inf")
        return float(min(state.ranks[world] for world in countermodels))

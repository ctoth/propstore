from __future__ import annotations

from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import World
from propstore.belief_set.ic_merge import _distance_to_formula


class CountingConjunctionFormula:
    def __init__(self, atoms: frozenset[str]) -> None:
        self._atoms = atoms
        self.evaluations = 0

    def evaluate(self, world: World) -> bool:
        self.evaluations += 1
        return self._atoms <= world

    def atoms(self) -> frozenset[str]:
        return self._atoms


def test_distance_to_formula_memo_reduces_repeated_six_var_scan_by_10x() -> None:
    signature = frozenset({"a", "b", "c", "d", "e", "f"})
    worlds = tuple(BeliefSet.all_worlds(signature))
    formula = CountingConjunctionFormula(signature)

    for world in worlds:
        _distance_to_formula(world, formula, signature)

    uncached_evaluation_budget = len(worlds) * len(worlds)
    assert formula.evaluations * 10 <= uncached_evaluation_budget

    after_first_pass = formula.evaluations
    for world in worlds:
        _distance_to_formula(world, formula, signature)

    assert formula.evaluations == after_first_pass

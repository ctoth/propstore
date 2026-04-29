from __future__ import annotations

import propstore.belief_set.ic_merge as ic_merge
from propstore.belief_set import Atom, conjunction


def test_ic_merge_distance_cache_is_keyed_by_formula_value() -> None:
    """Class A - must fail today: cache key is (id(formula), signature)."""

    formula_a = conjunction(Atom("p"), Atom("q"))
    formula_b = conjunction(Atom("p"), Atom("q"))
    signature = frozenset({"p", "q"})

    assert formula_a == formula_b
    assert formula_a is not formula_b

    ic_merge._DISTANCE_FORMULA_CACHE.clear()
    try:
        ic_merge._distance_to_formula(frozenset(), formula_a, signature)
        ic_merge._distance_to_formula(frozenset({"p"}), formula_b, signature)

        assert list(ic_merge._DISTANCE_FORMULA_CACHE) == [(formula_a, signature)]
    finally:
        ic_merge._DISTANCE_FORMULA_CACHE.clear()

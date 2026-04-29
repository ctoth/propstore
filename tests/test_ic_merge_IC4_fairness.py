from __future__ import annotations

import pytest

from propstore.belief_set import Atom, conjunction, negate
from propstore.belief_set.ic_merge import ICMergeOperator, merge_belief_profile


@pytest.mark.parametrize("operator", (ICMergeOperator.SIGMA, ICMergeOperator.GMAX))
def test_ic_merge_ic4_does_not_favor_one_consistent_source_over_another(
    operator: ICMergeOperator,
) -> None:
    """Class B - coverage gate for KPP 2002 IC4 fairness, p.4."""

    p = Atom("p")
    q = Atom("q")
    alphabet = frozenset({"p", "q"})
    mu = q
    left = conjunction(p, q)
    right = conjunction(negate(p), q)

    result = merge_belief_profile(alphabet, (left, right), mu, operator=operator)

    assert not result.belief_set.entails(negate(left))
    assert not result.belief_set.entails(negate(right))

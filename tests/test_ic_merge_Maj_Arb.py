from __future__ import annotations

from propstore.belief_set import Atom, BeliefSet, Formula, conjunction, disjunction, negate
from propstore.belief_set.core import align_belief_sets
from propstore.belief_set.ic_merge import ICMergeOperator, merge_belief_profile


def _entails(left: BeliefSet, right: BeliefSet) -> bool:
    aligned_left, aligned_right = align_belief_sets(left, right)
    return aligned_left.models <= aligned_right.models


def _implies(antecedent: Formula, consequent: Formula) -> Formula:
    return disjunction(negate(antecedent), consequent)


def test_ic_merge_sigma_satisfies_majority_postulate() -> None:
    """Class B - coverage gate for KPP 2002 majority, Theorem 4.2 p.13."""

    p = Atom("p")
    alphabet = frozenset({"p"})
    minority_profile = (negate(p),)
    majority_profile = (p,)

    dominant = merge_belief_profile(
        alphabet,
        majority_profile,
        p.or_(negate(p)),
        operator=ICMergeOperator.SIGMA,
    ).belief_set
    combined = merge_belief_profile(
        alphabet,
        minority_profile + majority_profile * 2,
        p.or_(negate(p)),
        operator=ICMergeOperator.SIGMA,
    ).belief_set

    assert _entails(combined, dominant)


def test_ic_merge_gmax_satisfies_arbitration_block_of_flats_example() -> None:
    """Class B - coverage gate for KPP 2002 arbitration, Theorem 4.14 p.791."""

    s = Atom("S")
    t = Atom("T")
    p = Atom("P")
    i = Atom("I")
    alphabet = frozenset({"S", "T", "P", "I"})
    two_or_more = disjunction(conjunction(s, t), conjunction(s, p), conjunction(t, p))
    mu = _implies(two_or_more, i)
    profile = (
        conjunction(s, t, p),
        conjunction(s, t, p),
        conjunction(negate(s), negate(t), negate(p), negate(i)),
        conjunction(t, p, negate(i)),
    )

    result = merge_belief_profile(alphabet, profile, mu, operator=ICMergeOperator.GMAX)

    assert result.belief_set.models == frozenset({
        frozenset({"P"}),
        frozenset({"T"}),
    })

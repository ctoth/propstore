"""Differential tests for the tree-decomposition exact backend.

These tests cross-check the public exact-DP routing against exact enumeration.
If the DP backend cannot maintain exactness, the public exact-DP surface is wrong.
"""

from __future__ import annotations

import random

import pytest

from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion, from_probability
from propstore.praf import ProbabilisticAF, compute_praf_acceptance


def _regression_praf() -> ProbabilisticAF:
    """Concrete randomized differential counterexample captured from RED search."""
    af = ArgumentationFramework(
        arguments=frozenset({"A", "B", "C", "D", "E", "F"}),
        defeats=frozenset(
            {
                ("B", "C"),
                ("B", "D"),
                ("B", "E"),
                ("C", "C"),
                ("C", "D"),
                ("D", "A"),
                ("D", "E"),
                ("E", "B"),
                ("E", "D"),
                ("F", "A"),
                ("F", "B"),
                ("F", "D"),
            }
        ),
    )
    return ProbabilisticAF(
        framework=af,
        p_args={
            "A": from_probability(0.833333, 10),
            "B": from_probability(0.833333, 10),
            "C": from_probability(0.5, 10),
            "D": from_probability(0.666667, 10),
            "E": Opinion.dogmatic_true(),
            "F": from_probability(0.666667, 10),
        },
        p_defeats={
            ("F", "D"): from_probability(0.416667, 10),
            ("E", "B"): from_probability(0.75, 10),
            ("E", "D"): from_probability(0.75, 10),
            ("B", "C"): from_probability(0.583333, 10),
            ("C", "C"): Opinion.dogmatic_true(),
            ("C", "D"): from_probability(0.583333, 10),
            ("D", "A"): from_probability(0.583333, 10),
            ("F", "A"): Opinion.dogmatic_true(),
            ("D", "E"): from_probability(0.583333, 10),
            ("F", "B"): Opinion.dogmatic_true(),
            ("B", "E"): from_probability(0.583333, 10),
            ("B", "D"): from_probability(0.583333, 10),
        },
    )


def _random_praf(seed: int) -> ProbabilisticAF:
    """Small deterministic generator for repeated public-route differential checks."""
    rng = random.Random(seed)
    size = rng.randint(2, 6)
    args = [chr(ord("A") + i) for i in range(size)]
    defeats = {
        (src, tgt)
        for src in args
        for tgt in args
        if rng.random() < 0.25
    }
    if not defeats:
        defeats.add((args[0], args[0]))
    af = ArgumentationFramework(arguments=frozenset(args), defeats=frozenset(defeats))
    p_args = {}
    for arg in args:
        probability = rng.choice([1.0, 0.9, 0.7, 0.5])
        p_args[arg] = (
            Opinion.dogmatic_true()
            if probability == 1.0
            else from_probability(probability, 10)
        )
    p_defeats = {}
    for edge in defeats:
        probability = rng.choice([1.0, 0.8, 0.6, 0.4])
        p_defeats[edge] = (
            Opinion.dogmatic_true()
            if probability == 1.0
            else from_probability(probability, 10)
    )
    return ProbabilisticAF(framework=af, p_args=p_args, p_defeats=p_defeats)


def _assert_acceptance_close(
    actual: dict[str, float],
    expected: dict[str, float],
    *,
    abs_tol: float = 1e-12,
) -> None:
    assert actual.keys() == expected.keys()
    for arg in actual:
        assert actual[arg] == pytest.approx(expected[arg], abs=abs_tol)


def test_exact_dp_matches_exact_enum_under_repeated_randomized_differential_runs():
    """Public exact routing must agree with exact enumeration on bounded instances."""
    for seed in range(20):
        praf = _random_praf(seed)
        exact = compute_praf_acceptance(praf, semantics="grounded", strategy="exact_enum")
        routed = compute_praf_acceptance(praf, semantics="grounded", strategy="exact_dp")

        assert routed.strategy_used == "exact_dp"
        _assert_acceptance_close(routed.acceptance_probs, exact.acceptance_probs)


def test_exact_dp_history_independence():
    """Prior exact evaluations must not change the result of a later exact query."""
    unrelated = _random_praf(999)
    compute_praf_acceptance(unrelated, semantics="grounded", strategy="exact_dp")

    praf = _regression_praf()
    exact = compute_praf_acceptance(praf, semantics="grounded", strategy="exact_enum")
    routed = compute_praf_acceptance(praf, semantics="grounded", strategy="exact_dp")

    assert routed.strategy_used == "exact_dp"
    _assert_acceptance_close(routed.acceptance_probs, exact.acceptance_probs)

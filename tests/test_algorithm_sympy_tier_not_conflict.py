from __future__ import annotations

from ast_equiv import Tier
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import patch

from propstore.cel_checker import ConceptInfo, KindType
from propstore.conflict_detector.algorithms import detect_algorithm_conflicts
from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable


def _claim(claim_id: str, body: str) -> ConflictClaim:
    return ConflictClaim(
        claim_id=claim_id,
        claim_type="algorithm",
        output_concept_id="out",
        body=body,
        variables=(ConflictClaimVariable(concept_id="in", symbol="x"),),
    )


def _registry() -> dict[str, ConceptInfo]:
    return {"x": ConceptInfo("in", "x", KindType.QUANTITY)}


def test_sympy_tier_equivalence_suppresses_algorithm_conflict() -> None:
    records = detect_algorithm_conflicts(
        [
            _claim("a", "def f(x):\n    return x + x\n"),
            _claim("b", "def f(x):\n    return 2 * x\n"),
        ],
        _registry(),
    )

    assert records == []


def test_partial_eval_equivalence_suppresses_algorithm_conflict(monkeypatch) -> None:
    from propstore.conflict_detector import algorithms

    class Result:
        equivalent = True
        tier = Tier.PARTIAL_EVAL
        similarity = 1.0

    monkeypatch.setattr(algorithms, "ast_compare", lambda *args, **kwargs: Result())

    records = algorithms.detect_algorithm_conflicts(
        [_claim("a", "def f(x):\n    return x\n"), _claim("b", "def f(x):\n    return x\n")],
        _registry(),
    )

    assert records == []


def test_none_tier_non_equivalence_still_reports_conflict(monkeypatch) -> None:
    from propstore.conflict_detector import algorithms

    class Result:
        equivalent = False
        tier = Tier.NONE
        similarity = 0.0

    monkeypatch.setattr(algorithms, "ast_compare", lambda *args, **kwargs: Result())

    records = algorithms.detect_algorithm_conflicts(
        [_claim("a", "def f(x):\n    return x\n"), _claim("b", "def f(x):\n    return x + 1\n")],
        _registry(),
    )

    assert len(records) == 1


@pytest.mark.property
@given(tier=st.sampled_from([Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL]))
@settings(deadline=None, max_examples=12)
def test_generated_true_equivalence_tiers_suppress_conflict(tier: Tier) -> None:
    from propstore.conflict_detector import algorithms

    class Result:
        equivalent = True
        similarity = 1.0

        def __init__(self, tier: Tier) -> None:
            self.tier = tier

    with patch.object(algorithms, "ast_compare", lambda *args, **kwargs: Result(tier)):
        records = algorithms.detect_algorithm_conflicts(
            [_claim("a", "def f(x):\n    return x\n"), _claim("b", "def f(x):\n    return x\n")],
            _registry(),
        )

    assert records == []

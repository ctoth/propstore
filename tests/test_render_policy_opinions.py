"""Tests for render policy decision criterion extensions.

Decision criteria determine how opinion uncertainty maps to actionable
values at render time. Per Denoeux (2019, p.17-18): pignistic is the
default; Hurwicz, lower_bound, upper_bound give users control over
how uncertainty is handled.
"""

from __future__ import annotations

import pytest

from propstore.opinion import Opinion
from propstore.world.types import ReasoningBackend, RenderPolicy, ResolutionStrategy, apply_decision_criterion


# ── 1. Default decision criterion ───────────────────────────────

def test_default_decision_criterion_is_pignistic():
    """Per Denoeux (2019, p.17-18): pignistic transformation is the default decision criterion."""
    policy = RenderPolicy()
    assert policy.decision_criterion == "pignistic"


# ── 2. Pignistic equals expectation ─────────────────────────────

def test_pignistic_equals_expectation():
    """Per Jøsang (2001, p.5, Def 6): E(ω) = b + a·u.

    The pignistic criterion must match the existing confidence column value
    (which is Opinion.expectation()).
    """
    # Opinion with known components: b=0.6, d=0.1, u=0.3, a=0.5
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    op = Opinion(b, d, u, a)
    expected = op.expectation()  # 0.6 + 0.5 * 0.3 = 0.75

    result = apply_decision_criterion(b, d, u, a, confidence=expected, criterion="pignistic")
    assert result == pytest.approx(expected)
    assert result == pytest.approx(0.75)


# ── 3. Lower bound equals belief ────────────────────────────────

def test_lower_bound_equals_belief():
    """Per Jøsang (2001, p.4): Bel(x) = b."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="lower_bound")
    assert result == pytest.approx(b)
    assert result == pytest.approx(0.6)


# ── 4. Upper bound equals plausibility ──────────────────────────

def test_upper_bound_equals_plausibility():
    """Per Jøsang (2001, p.4): Pl(x) = 1 - d."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="upper_bound")
    assert result == pytest.approx(1.0 - d)
    assert result == pytest.approx(0.9)


# ── 5. Hurwicz interpolates ─────────────────────────────────────

def test_hurwicz_interpolates():
    """Per Denoeux (2019, p.17): Hurwicz criterion = α·Bel + (1-α)·Pl.

    With α=0.5: 0.5 * 0.6 + 0.5 * 0.9 = 0.75.
    """
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(
        b, d, u, a, confidence=0.75,
        criterion="hurwicz", pessimism_index=0.5,
    )
    bel = b          # 0.6
    pl = 1.0 - d     # 0.9
    expected = 0.5 * bel + 0.5 * pl  # 0.75
    assert result == pytest.approx(expected)


# ── 6. Hurwicz at extremes ──────────────────────────────────────

def test_hurwicz_at_extremes():
    """Hurwicz at α=1.0 equals lower_bound, at α=0.0 equals upper_bound."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5

    pessimistic = apply_decision_criterion(
        b, d, u, a, confidence=0.75,
        criterion="hurwicz", pessimism_index=1.0,
    )
    lower = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="lower_bound")
    assert pessimistic == pytest.approx(lower)

    optimistic = apply_decision_criterion(
        b, d, u, a, confidence=0.75,
        criterion="hurwicz", pessimism_index=0.0,
    )
    upper = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="upper_bound")
    assert optimistic == pytest.approx(upper)


# ── 7. Show uncertainty interval ────────────────────────────────

def test_show_uncertainty_interval():
    """Interval [b, 1-d] per Jøsang (2001, p.4).

    When show_uncertainty_interval=True, output includes the [Bel, Pl] interval.
    """
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    op = Opinion(b, d, u, a)
    bel, pl = op.uncertainty_interval()
    assert bel == pytest.approx(b)
    assert pl == pytest.approx(1.0 - d)

    # RenderPolicy field exists and defaults to False
    policy = RenderPolicy()
    assert policy.show_uncertainty_interval is False

    policy_on = RenderPolicy(show_uncertainty_interval=True)
    assert policy_on.show_uncertainty_interval is True


# ── 8. RenderPolicy serialization roundtrip ───────────────────

def test_worldline_policy_serialization_roundtrip():
    """RenderPolicy with worldline-used fields serializes to dict and back without loss."""
    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
        strategy=ResolutionStrategy.ARGUMENTATION,
        decision_criterion="hurwicz",
        pessimism_index=0.7,
        show_uncertainty_interval=True,
    )
    d = policy.to_dict()
    restored = RenderPolicy.from_dict(d)
    assert restored.decision_criterion == "hurwicz"
    assert restored.pessimism_index == pytest.approx(0.7)
    assert restored.show_uncertainty_interval is True


# ── 9. RenderPolicy defaults via dict parsing ──────────────────────────

def test_worldline_policy_backward_compat():
    """RenderPolicy.from_dict({}) uses defaults for worldline-used fields."""
    policy = RenderPolicy.from_dict({})
    assert policy.decision_criterion == "pignistic"
    assert policy.pessimism_index == pytest.approx(0.5)
    assert policy.show_uncertainty_interval is False


# ── 10. Vacuous opinion all criteria ─────────────────────────────

def test_vacuous_opinion_all_criteria():
    """For vacuous opinion (0, 0, 1, 0.5): all criteria produce correct results on total ignorance.

    pignistic = 0.5, lower_bound = 0.0, upper_bound = 1.0, hurwicz(0.5) = 0.5.
    """
    b, d, u, a = 0.0, 0.0, 1.0, 0.5

    pignistic = apply_decision_criterion(b, d, u, a, confidence=0.5, criterion="pignistic")
    assert pignistic == pytest.approx(0.5)

    lower = apply_decision_criterion(b, d, u, a, confidence=0.5, criterion="lower_bound")
    assert lower == pytest.approx(0.0)

    upper = apply_decision_criterion(b, d, u, a, confidence=0.5, criterion="upper_bound")
    assert upper == pytest.approx(1.0)

    hurwicz = apply_decision_criterion(
        b, d, u, a, confidence=0.5,
        criterion="hurwicz", pessimism_index=0.5,
    )
    assert hurwicz == pytest.approx(0.5)


# ── Fallback: None opinion uses raw confidence ───────────────────

def test_fallback_to_confidence_when_opinion_missing():
    """When opinion columns are NULL (old data), fall back to raw confidence."""
    result = apply_decision_criterion(
        None, None, None, None, confidence=0.8, criterion="pignistic",
    )
    assert result == pytest.approx(0.8)

    result_none = apply_decision_criterion(
        None, None, None, None, confidence=None, criterion="pignistic",
    )
    assert result_none is None

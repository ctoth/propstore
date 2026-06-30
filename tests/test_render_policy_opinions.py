"""Render-time decision criteria over opinions (Phase 10-5, deferred row A5).

``apply_decision_criterion`` maps a stored Jøsang opinion tuple to a single
actionable value at render time, tagging the result so a calibrated-opinion value
is never confused with total absence of data. Per Smets & Kennes (1994, p.202) the
pignistic transform is the default; lower/upper bounds and Hurwicz give users
control over how uncertainty is handled.

Page-image grounding:
papers/Josang_2001_LogicUncertainProbabilities/pngs/page-004.png
papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png
"""

from __future__ import annotations

import pytest
from doxa import Opinion
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.world.types import (
    DecisionValueSource,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
    apply_decision_criterion,
)


# ── Default decision criterion ──────────────────────────────────


def test_default_decision_criterion_is_pignistic() -> None:
    assert RenderPolicy().decision_criterion == "pignistic"


def test_pignistic_is_betp_for_binomial_opinion() -> None:
    """Smets & Kennes (1994, p.202): BetP(x) = b + u/2 for a binomial opinion."""

    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=None, criterion="pignistic")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(b + u / 2.0)
    assert result.value == pytest.approx(0.75)


def test_projected_probability_equals_expectation() -> None:
    """Jøsang (2001, Def 6, p.5): E(ω) = b + a·u."""

    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    op = Opinion(b, d, u, a)
    result = apply_decision_criterion(
        b, d, u, a, confidence=None, criterion="projected_probability"
    )
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(op.expectation())


def test_lower_bound_equals_belief() -> None:
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=None, criterion="lower_bound")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(b)


def test_upper_bound_equals_plausibility() -> None:
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=None, criterion="upper_bound")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(1.0 - d)


def test_hurwicz_interpolates_and_hits_extremes() -> None:
    """Denoeux (2019, p.17): Hurwicz = α·Bel + (1-α)·Pl."""

    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    bel, pl = b, 1.0 - d

    mid = apply_decision_criterion(
        b, d, u, a, confidence=None, criterion="hurwicz", pessimism_index=0.5
    )
    assert mid.source is DecisionValueSource.OPINION
    assert mid.value == pytest.approx(0.5 * bel + 0.5 * pl)

    pessimistic = apply_decision_criterion(
        b, d, u, a, confidence=None, criterion="hurwicz", pessimism_index=1.0
    )
    optimistic = apply_decision_criterion(
        b, d, u, a, confidence=None, criterion="hurwicz", pessimism_index=0.0
    )
    assert pessimistic.value == pytest.approx(bel)
    assert optimistic.value == pytest.approx(pl)


def test_vacuous_opinion_decision_values() -> None:
    """Total ignorance (0, 0, 1, a): bounds span [0, 1], pignistic = 0.5."""

    b, d, u, a = 0.0, 0.0, 1.0, 0.5
    pignistic = apply_decision_criterion(b, d, u, a, confidence=None, criterion="pignistic")
    lower = apply_decision_criterion(b, d, u, a, confidence=None, criterion="lower_bound")
    upper = apply_decision_criterion(b, d, u, a, confidence=None, criterion="upper_bound")
    assert pignistic.value == pytest.approx(0.5)
    assert lower.value == pytest.approx(0.0)
    assert upper.value == pytest.approx(1.0)


# ── Honest ignorance: missing opinion is never raw confidence ───


def test_missing_opinion_is_no_data_not_confidence() -> None:
    result = apply_decision_criterion(
        None, None, None, None, confidence=0.8, criterion="pignistic"
    )
    assert result.source is DecisionValueSource.NO_DATA
    assert result.value is None


@pytest.mark.parametrize(
    "components",
    [
        (None, 0.1, 0.2, 0.5),
        (0.7, None, 0.2, 0.5),
        (0.7, 0.1, None, 0.5),
        (0.7, 0.1, 0.2, None),
    ],
)
def test_partial_opinion_is_no_data(
    components: tuple[float | None, float | None, float | None, float | None],
) -> None:
    b, d, u, a = components
    result = apply_decision_criterion(b, d, u, a, confidence=0.8, criterion="pignistic")
    assert result.source is DecisionValueSource.NO_DATA
    assert result.value is None


# ── Uncertainty interval ────────────────────────────────────────


def test_uncertainty_interval_is_belief_plausibility() -> None:
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    bel, pl = Opinion(b, d, u, a).uncertainty_interval()
    assert bel == pytest.approx(b)
    assert pl == pytest.approx(1.0 - d)
    assert RenderPolicy().show_uncertainty_interval is False
    assert RenderPolicy(show_uncertainty_interval=True).show_uncertainty_interval is True


# ── RenderPolicy serialization ──────────────────────────────────


def test_render_policy_opinion_fields_roundtrip() -> None:
    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
        strategy=ResolutionStrategy.ARGUMENTATION,
        decision_criterion="hurwicz",
        pessimism_index=0.7,
        show_uncertainty_interval=True,
    )
    restored = RenderPolicy.from_dict(policy.to_dict())
    assert restored.decision_criterion == "hurwicz"
    assert restored.pessimism_index == pytest.approx(0.7)
    assert restored.show_uncertainty_interval is True


def test_render_policy_defaults_from_empty_dict() -> None:
    policy = RenderPolicy.from_dict({})
    assert policy.decision_criterion == "pignistic"
    assert policy.pessimism_index == pytest.approx(0.5)
    assert policy.show_uncertainty_interval is False


# ── Property: decision values stay inside [Bel, Pl] ─────────────


@st.composite
def valid_decision_opinions(
    draw: st.DrawFn,
) -> tuple[float, float, float, float]:
    u = draw(st.floats(min_value=0.0, max_value=1.0))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    assume(abs(b + d + u - 1.0) < 1e-9)
    return b, d, u, a


@pytest.mark.property
@given(valid_decision_opinions())
@settings(deadline=None)
def test_decision_values_stay_inside_belief_plausibility(
    opinion: tuple[float, float, float, float],
) -> None:
    b, d, u, a = opinion
    bel, pl = b, 1.0 - d
    for criterion in ("pignistic", "projected_probability", "lower_bound", "upper_bound"):
        result = apply_decision_criterion(b, d, u, a, confidence=None, criterion=criterion)
        assert result.source is DecisionValueSource.OPINION
        assert result.value is not None
        assert bel - 1e-9 <= result.value <= pl + 1e-9

    hurwicz = apply_decision_criterion(
        b, d, u, a, confidence=None, criterion="hurwicz", pessimism_index=0.37
    )
    assert hurwicz.value is not None
    assert bel - 1e-9 <= hurwicz.value <= pl + 1e-9

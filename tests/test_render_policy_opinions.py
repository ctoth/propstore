"""Tests for render policy decision criterion extensions.

Decision criteria determine how opinion uncertainty maps to actionable
values at render time. Per Denoeux (2019, p.17-18): pignistic is the
default; Hurwicz, lower_bound, upper_bound give users control over
how uncertainty is handled.
"""

from __future__ import annotations

import pytest

from propstore.opinion import Opinion
from propstore.world.types import (
    DecisionValueSource,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
    apply_decision_criterion,
)


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
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(expected)
    assert result.value == pytest.approx(0.75)


# ── 3. Lower bound equals belief ────────────────────────────────

def test_lower_bound_equals_belief():
    """Per Jøsang (2001, p.4): Bel(x) = b."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="lower_bound")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(b)
    assert result.value == pytest.approx(0.6)


# ── 4. Upper bound equals plausibility ──────────────────────────

def test_upper_bound_equals_plausibility():
    """Per Jøsang (2001, p.4): Pl(x) = 1 - d."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="upper_bound")
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(1.0 - d)
    assert result.value == pytest.approx(0.9)


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
    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(expected)


# ── 6. Hurwicz at extremes ──────────────────────────────────────

def test_hurwicz_at_extremes():
    """Hurwicz at α=1.0 equals lower_bound, at α=0.0 equals upper_bound."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5

    pessimistic = apply_decision_criterion(
        b, d, u, a, confidence=0.75,
        criterion="hurwicz", pessimism_index=1.0,
    )
    lower = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="lower_bound")
    assert pessimistic.source is DecisionValueSource.OPINION
    assert lower.source is DecisionValueSource.OPINION
    assert pessimistic.value == pytest.approx(lower.value)

    optimistic = apply_decision_criterion(
        b, d, u, a, confidence=0.75,
        criterion="hurwicz", pessimism_index=0.0,
    )
    upper = apply_decision_criterion(b, d, u, a, confidence=0.75, criterion="upper_bound")
    assert optimistic.source is DecisionValueSource.OPINION
    assert upper.source is DecisionValueSource.OPINION
    assert optimistic.value == pytest.approx(upper.value)


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
    assert pignistic.source is DecisionValueSource.OPINION
    assert pignistic.value == pytest.approx(0.5)

    lower = apply_decision_criterion(b, d, u, a, confidence=0.5, criterion="lower_bound")
    assert lower.source is DecisionValueSource.OPINION
    assert lower.value == pytest.approx(0.0)

    upper = apply_decision_criterion(b, d, u, a, confidence=0.5, criterion="upper_bound")
    assert upper.source is DecisionValueSource.OPINION
    assert upper.value == pytest.approx(1.0)

    hurwicz = apply_decision_criterion(
        b, d, u, a, confidence=0.5,
        criterion="hurwicz", pessimism_index=0.5,
    )
    assert hurwicz.source is DecisionValueSource.OPINION
    assert hurwicz.value == pytest.approx(0.5)


# ── Fallback: None opinion uses raw confidence ───────────────────

def test_fallback_to_confidence_when_opinion_missing():
    """When opinion columns are NULL (old data), fall back to raw confidence.

    The tagged return must mark the difference between a calibrated opinion
    result and a confidence passthrough, per the honest-ignorance discipline.
    """
    result = apply_decision_criterion(
        None, None, None, None, confidence=0.8, criterion="pignistic",
    )
    assert result.source is DecisionValueSource.CONFIDENCE_FALLBACK
    assert result.value == pytest.approx(0.8)

    result_none = apply_decision_criterion(
        None, None, None, None, confidence=None, criterion="pignistic",
    )
    assert result_none.source is DecisionValueSource.NO_DATA
    assert result_none.value is None


# ── 11. Lifecycle-visibility flags (WS-Z-gates Phase 4) ─────────────

def test_lifecycle_visibility_flags_default_false():
    """Per reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md
    (exit criteria): default policy hides ``stage='draft'``,
    ``build_status='blocked'``, ``promotion_status='blocked'`` rows, and does
    NOT surface ``build_diagnostics`` rows. The three RenderPolicy visibility
    flags default to ``False`` to preserve that "don't show problems by
    default" posture.
    """
    policy = RenderPolicy()
    assert policy.include_drafts is False
    assert policy.include_blocked is False
    assert policy.show_quarantined is False


def test_lifecycle_visibility_flags_round_trip():
    """Per ws-z-render-gates.md (axis-1 findings 3.1/3.2/3.3 closure): the
    three visibility flags are user-configurable opt-ins. They must survive
    the ``to_dict`` / ``from_dict`` serialization round-trip identically so
    ``--policy-json`` plumbing and equivalent persistence paths preserve
    them.
    """
    policy = RenderPolicy(
        include_drafts=True,
        include_blocked=True,
        show_quarantined=True,
    )
    restored = RenderPolicy.from_dict(policy.to_dict())
    assert restored.include_drafts is True
    assert restored.include_blocked is True
    assert restored.show_quarantined is True


def test_lifecycle_visibility_flags_omit_when_default():
    """Per propstore/world/types.py ``to_dict`` convention: fields at their
    default value are omitted from the serialized dict. The three lifecycle
    visibility flags follow that pattern — a default-configured policy
    produces a dict that does NOT contain ``include_drafts``,
    ``include_blocked``, or ``show_quarantined`` keys.
    """
    default = RenderPolicy()
    payload = default.to_dict()
    assert "include_drafts" not in payload
    assert "include_blocked" not in payload
    assert "show_quarantined" not in payload

    # Inverse: enabling one flag surfaces it in the dict.
    flagged = RenderPolicy(include_drafts=True)
    flagged_payload = flagged.to_dict()
    assert flagged_payload["include_drafts"] is True
    assert "include_blocked" not in flagged_payload
    assert "show_quarantined" not in flagged_payload

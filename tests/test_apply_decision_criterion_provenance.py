"""Tests for the typed-provenance return of `apply_decision_criterion`.

Per the honest-ignorance discipline (CLAUDE.md): a calibrated opinion result
must be distinguishable from a raw confidence fallback at the type level.
`apply_decision_criterion` returns `DecisionValue(value, source)` where
`source` is a `DecisionValueSource` enum with three variants:

- ``OPINION``: all four opinion components were present and the value was
  computed via the requested criterion (pignistic / lower_bound / upper_bound
  / hurwicz).
- ``CONFIDENCE_FALLBACK``: the opinion tuple was incomplete but the legacy
  ``confidence`` scalar was present and was returned as-is.
- ``NO_DATA``: neither the opinion tuple nor the confidence were present.
  ``value`` is ``None``.
"""

from __future__ import annotations

import pytest

from propstore.world.types import (
    DecisionValue,
    DecisionValueSource,
    apply_decision_criterion,
)


def test_full_opinion_tagged_as_opinion():
    """All four opinion components present + pignistic → source is OPINION."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    result = apply_decision_criterion(
        b, d, u, a, confidence=0.99, criterion="pignistic",
    )
    assert isinstance(result, DecisionValue)
    assert result.source is DecisionValueSource.OPINION
    # Pignistic: b + a*u = 0.6 + 0.5 * 0.3 = 0.75. The confidence kwarg
    # must NOT leak through when the opinion tuple is complete.
    assert result.value == pytest.approx(0.75)


def test_missing_opinion_with_confidence_tagged_as_fallback():
    """All four opinion components None + confidence set → CONFIDENCE_FALLBACK."""
    result = apply_decision_criterion(
        None, None, None, None, confidence=0.75, criterion="pignistic",
    )
    assert isinstance(result, DecisionValue)
    assert result.source is DecisionValueSource.CONFIDENCE_FALLBACK
    assert result.value == pytest.approx(0.75)


def test_partial_opinion_tagged_as_fallback():
    """Partial opinion tuple (e.g. b set, u missing) + confidence → CONFIDENCE_FALLBACK.

    The current implementation requires *all four* opinion components to be
    present before computing from opinion. Any None among the four falls
    through to the confidence path. This test pins that contract under the
    new tagged return.
    """
    result = apply_decision_criterion(
        0.6, 0.1, None, 0.5, confidence=0.4, criterion="pignistic",
    )
    assert isinstance(result, DecisionValue)
    assert result.source is DecisionValueSource.CONFIDENCE_FALLBACK
    assert result.value == pytest.approx(0.4)


def test_no_data_returns_no_data_with_none_value():
    """All inputs None → source is NO_DATA, value is None."""
    result = apply_decision_criterion(
        None, None, None, None, confidence=None, criterion="pignistic",
    )
    assert isinstance(result, DecisionValue)
    assert result.source is DecisionValueSource.NO_DATA
    assert result.value is None


def test_hurwicz_criterion_with_full_opinion():
    """Hurwicz branch: source is OPINION, value = α·Bel + (1-α)·Pl."""
    b, d, u, a = 0.6, 0.1, 0.3, 0.5
    pessimism = 0.7
    result = apply_decision_criterion(
        b, d, u, a, confidence=0.99,
        criterion="hurwicz", pessimism_index=pessimism,
    )
    assert isinstance(result, DecisionValue)
    assert result.source is DecisionValueSource.OPINION
    bel = b              # 0.6
    pl = 1.0 - d         # 0.9
    expected = pessimism * bel + (1.0 - pessimism) * pl  # 0.7*0.6 + 0.3*0.9 = 0.42 + 0.27 = 0.69
    assert result.value == pytest.approx(expected)

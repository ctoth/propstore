"""Property checks for WBF base-rate and clamp consistency."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.opinion import Opinion, wbf


@st.composite
def _opinion_pairs(draw):
    opinions: list[Opinion] = []
    for _ in range(2):
        base_rate = draw(st.floats(min_value=0.001, max_value=0.999))
        uncertainty = draw(st.floats(min_value=0.01, max_value=0.99))
        remaining = 1.0 - uncertainty
        belief = draw(st.floats(min_value=0.0, max_value=remaining))
        disbelief = remaining - belief
        opinions.append(Opinion(belief, disbelief, uncertainty, base_rate))
    return tuple(opinions)


@pytest.mark.property
@given(_opinion_pairs())
@settings(deadline=None)
def test_wbf_base_rate_is_confidence_weighted_without_clamp(pair) -> None:
    """vdH 2018 Def 4 (p.5) computes a_hat from confidence weights."""
    left, right = pair

    fused = wbf(left, right)
    reversed_fused = wbf(right, left)
    expected_a = (
        left.a * (1.0 - left.u) + right.a * (1.0 - right.u)
    ) / ((1.0 - left.u) + (1.0 - right.u))

    assert fused.b + fused.d + fused.u == pytest.approx(1.0, abs=1e-9)
    assert 0.0 <= fused.b <= 1.0
    assert 0.0 <= fused.d <= 1.0
    assert 0.0 <= fused.u <= 1.0
    assert fused.a == pytest.approx(expected_a, abs=1e-12)
    assert fused.b == pytest.approx(reversed_fused.b, abs=1e-12)
    assert fused.d == pytest.approx(reversed_fused.d, abs=1e-12)
    assert fused.u == pytest.approx(reversed_fused.u, abs=1e-12)
    assert fused.a == pytest.approx(reversed_fused.a, abs=1e-12)


def test_wbf_base_rate_is_not_clamped_to_propstore_convention() -> None:
    """Def 4 keeps valid low base rates; `_BASE_RATE_CLAMP` is not applied."""
    fused = wbf(
        Opinion(0.2, 0.3, 0.5, 0.001),
        Opinion(0.1, 0.4, 0.5, 0.001),
    )

    assert fused.a == pytest.approx(0.001, abs=1e-12)

"""Phase 10-2: float query-parameter boundary handling in the web adapter."""

from __future__ import annotations

import pytest

from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
)


def test_pessimism_index_accepts_inclusive_bounds() -> None:
    assert parse_render_policy_request({"pessimism_index": "0"}).pessimism_index == 0.0
    assert parse_render_policy_request({"pessimism_index": "1"}).pessimism_index == 1.0


def test_pessimism_index_rejects_out_of_range() -> None:
    with pytest.raises(WebQueryParseError, match="pessimism_index"):
        parse_render_policy_request({"pessimism_index": "1.5"})


def test_praf_confidence_rejects_exclusive_bounds() -> None:
    with pytest.raises(WebQueryParseError, match="praf_confidence"):
        parse_render_policy_request({"praf_confidence": "1"})
    with pytest.raises(WebQueryParseError, match="praf_confidence"):
        parse_render_policy_request({"praf_confidence": "0"})


def test_praf_epsilon_rejects_zero_but_accepts_small_positive() -> None:
    with pytest.raises(WebQueryParseError, match="praf_epsilon"):
        parse_render_policy_request({"praf_epsilon": "0"})
    assert parse_render_policy_request({"praf_epsilon": "0.001"}).praf_epsilon == 0.001


def test_non_finite_float_is_rejected() -> None:
    for value in ("nan", "inf", "-inf"):
        with pytest.raises(WebQueryParseError, match="finite"):
            parse_render_policy_request({"pessimism_index": value})


def test_non_numeric_float_is_rejected() -> None:
    with pytest.raises(WebQueryParseError, match="number"):
        parse_render_policy_request({"pessimism_index": "high"})

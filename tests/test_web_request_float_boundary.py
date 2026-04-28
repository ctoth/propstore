from __future__ import annotations

from hypothesis import given, strategies as st
import pytest

from propstore.web.requests import WebQueryParseError, parse_render_policy_request


FLOAT_PARAMS = ("pessimism_index", "praf_epsilon", "praf_confidence")


@pytest.mark.property
@given(st.sampled_from(FLOAT_PARAMS), st.sampled_from(("nan", "inf", "-inf")))
def test_float_query_params_reject_non_finite_values(name: str, value: str) -> None:
    with pytest.raises(WebQueryParseError):
        parse_render_policy_request({name: value})


@pytest.mark.property
@given(st.one_of(st.floats(max_value=-0.001, allow_nan=False), st.floats(min_value=1.001, allow_nan=False)))
def test_pessimism_index_must_be_between_zero_and_one(value: float) -> None:
    with pytest.raises(WebQueryParseError):
        parse_render_policy_request({"pessimism_index": str(value)})


@pytest.mark.property
@given(st.floats(max_value=0.0, allow_nan=False, allow_infinity=False))
def test_praf_epsilon_must_be_positive(value: float) -> None:
    with pytest.raises(WebQueryParseError):
        parse_render_policy_request({"praf_epsilon": str(value)})


@pytest.mark.property
@given(st.one_of(st.floats(max_value=0.0, allow_nan=False), st.floats(min_value=1.0, allow_nan=False)))
def test_praf_confidence_must_be_open_unit_interval(value: float) -> None:
    with pytest.raises(WebQueryParseError):
        parse_render_policy_request({"praf_confidence": str(value)})

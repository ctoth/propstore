"""HTTP request parsing helpers for web routes."""

from __future__ import annotations

from collections.abc import Mapping
import math

from propstore.app.rendering import AppRenderPolicyRequest
from propstore.app.repository_views import AppRepositoryViewRequest


class WebQueryParseError(Exception):
    """Raised when HTTP query parameters cannot build an app request."""


def parse_render_policy_request(params: Mapping[str, str | None]) -> AppRenderPolicyRequest:
    return AppRenderPolicyRequest(
        reasoning_backend=params.get("reasoning_backend") or "claim_graph",
        strategy=_optional_text(params.get("strategy")),
        semantics=params.get("semantics") or "grounded",
        set_comparison=params.get("set_comparison") or "elitist",
        decision_criterion=params.get("decision_criterion") or "pignistic",
        pessimism_index=_float_param(
            params,
            "pessimism_index",
            0.5,
            minimum=0.0,
            maximum=1.0,
        ),
        praf_strategy=params.get("praf_strategy") or "auto",
        praf_epsilon=_float_param(
            params,
            "praf_epsilon",
            0.01,
            minimum=0.0,
            include_minimum=False,
        ),
        praf_confidence=_float_param(
            params,
            "praf_confidence",
            0.95,
            minimum=0.0,
            maximum=1.0,
            include_minimum=False,
            include_maximum=False,
        ),
        praf_seed=_int_param(params, "praf_seed"),
        include_drafts=_bool_param(params, "include_drafts"),
        include_blocked=_bool_param(params, "include_blocked"),
        show_quarantined=_bool_param(params, "show_quarantined"),
    )


def parse_repository_view_request(params: Mapping[str, str | None]) -> AppRepositoryViewRequest:
    return AppRepositoryViewRequest(
        branch=_optional_text(params.get("branch")),
        revision=_optional_text(params.get("rev")),
    )


def _optional_text(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


def _bool_param(params: Mapping[str, str | None], name: str) -> bool:
    value = params.get(name)
    if value is None or value == "":
        return False
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise WebQueryParseError(f"{name} must be a boolean value")


def _float_param(
    params: Mapping[str, str | None],
    name: str,
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    include_minimum: bool = True,
    include_maximum: bool = True,
) -> float:
    value = params.get(name)
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError:
        raise WebQueryParseError(f"{name} must be a number") from None
    if not math.isfinite(parsed):
        raise WebQueryParseError(f"{name} must be finite")
    if minimum is not None and (
        parsed < minimum or (parsed == minimum and not include_minimum)
    ):
        comparator = "greater than or equal to" if include_minimum else "greater than"
        raise WebQueryParseError(f"{name} must be {comparator} {minimum:g}")
    if maximum is not None and (
        parsed > maximum or (parsed == maximum and not include_maximum)
    ):
        comparator = "less than or equal to" if include_maximum else "less than"
        raise WebQueryParseError(f"{name} must be {comparator} {maximum:g}")
    return parsed


def _int_param(params: Mapping[str, str | None], name: str) -> int | None:
    value = params.get(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise WebQueryParseError(f"{name} must be an integer") from None

"""Phase 10-2: the FastAPI app skeleton and request/serialization helpers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from propstore.web.app import create_app
from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
)


def test_create_app_is_shallow_fastapi_app() -> None:
    app = create_app()

    assert app.title == "propstore.web"
    assert any(getattr(route, "path", None) == "/healthz" for route in app.routes)


def test_healthz_reports_ok() -> None:
    response = TestClient(create_app()).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_app_serves_static_assets() -> None:
    response = TestClient(create_app()).get("/static/web.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_parse_render_policy_request_uses_web_input_only() -> None:
    request = parse_render_policy_request(
        {
            "reasoning_backend": "praf",
            "strategy": "argumentation",
            "include_drafts": "true",
            "praf_seed": "42",
        }
    )

    assert request.reasoning_backend == "praf"
    assert request.strategy == "argumentation"
    assert request.include_drafts is True
    assert request.praf_seed == 42


def test_parse_render_policy_request_defaults_are_honest() -> None:
    request = parse_render_policy_request({})

    assert request.reasoning_backend == "claim_graph"
    assert request.strategy is None
    assert request.include_drafts is False
    assert request.pessimism_index == 0.5


def test_parse_render_policy_request_rejects_invalid_bool() -> None:
    with pytest.raises(WebQueryParseError, match="include_drafts"):
        parse_render_policy_request({"include_drafts": "sometimes"})

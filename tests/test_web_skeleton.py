from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import pytest

from propstore.web.app import create_app
from propstore.web.requests import (
    WebQueryParseError,
    parse_render_policy_request,
    parse_repository_view_request,
)
from propstore.web.serialization import WebSerializationError, to_json_compatible


class _Mode(StrEnum):
    READY = "ready"


@dataclass(frozen=True)
class _NestedReport:
    mode: _Mode
    path: Path
    states: tuple[str, ...]


@dataclass(frozen=True)
class _Report:
    name: str
    nested: _NestedReport


def test_create_app_is_shallow_fastapi_app() -> None:
    app = create_app()

    assert app.title == "propstore.web"
    assert any(route.path == "/healthz" for route in app.routes)


def test_create_app_serves_static_assets() -> None:
    from fastapi.testclient import TestClient

    response = TestClient(create_app()).get("/static/web.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_parse_render_policy_request_uses_web_input_only_for_app_request() -> None:
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


def test_parse_render_policy_request_rejects_invalid_bool() -> None:
    with pytest.raises(WebQueryParseError, match="include_drafts"):
        parse_render_policy_request({"include_drafts": "sometimes"})


def test_parse_repository_view_request_parses_branch_and_revision() -> None:
    request = parse_repository_view_request(
        {
            "branch": "feature",
            "rev": "abc123",
        }
    )

    assert request.branch == "feature"
    assert request.revision == "abc123"


def test_to_json_compatible_serializes_dataclass_reports() -> None:
    payload = to_json_compatible(
        _Report(
            name="claim",
            nested=_NestedReport(
                mode=_Mode.READY,
                path=Path("knowledge"),
                states=("unknown", "blocked"),
            ),
        )
    )

    assert payload == {
        "name": "claim",
        "nested": {
            "mode": "ready",
            "path": "knowledge",
            "states": ["unknown", "blocked"],
        },
    }


def test_to_json_compatible_rejects_arbitrary_objects() -> None:
    with pytest.raises(WebSerializationError, match="unsupported"):
        to_json_compatible(object())

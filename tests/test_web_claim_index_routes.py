from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
import pytest

from propstore.app.claim_views import ClaimSummaryEntry, ClaimSummaryReport
from propstore.repository import Repository
from propstore.web import routing
from propstore.web.app import create_app


def _repo() -> Repository:
    return cast(Repository, object())


def _report() -> ClaimSummaryReport:
    return ClaimSummaryReport(
        entries=(
            ClaimSummaryEntry(
                claim_id="claim1",
                logical_id="paper:claim1",
                concept_id="concept1",
                concept_name="fundamental_frequency",
                concept_display="fundamental_frequency",
                claim_type="parameter",
                value_display="100 Hz",
                condition_display="(vacuous)",
                status_state="known",
                status_reason="Claim is visible under the current render policy.",
            ),
        )
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_claim_index_html_route_renders_inventory(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "list_claim_views", lambda repo, request: _report())

    response = client.get("/claims?concept=fundamental_frequency")

    assert response.status_code == 200
    html = response.text
    assert html.count("<h1>") == 1
    assert "Claims" in html
    assert "Claim Inventory" in html
    assert "fundamental_frequency" in html
    assert "/claim/claim1" in html
    assert "<th scope=\"col\">Concept(s)</th>" in html
    assert "<th scope=\"col\">Status</th>" in html


def test_claim_index_json_route_uses_search_report_when_query_present(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "search_claim_views", lambda repo, request: _report())

    response = client.get("/claims.json?q=frequency")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entries"][0]["claim_id"] == "claim1"
    assert payload["entries"][0]["concept_name"] == "fundamental_frequency"


def test_claim_index_route_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/claims.json?limit=0")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"

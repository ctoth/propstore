from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
import pytest

from propstore.app.concepts import (
    ConceptListEntry,
    ConceptListReport,
    ConceptSearchHit,
    ConceptSearchReport,
    ConceptSidecarMissingError,
)
from propstore.repository import Repository
from propstore.web import routing
from propstore.web.app import create_app


def _repo() -> Repository:
    return cast(Repository, object())


def _list_report() -> ConceptListReport:
    return ConceptListReport(
        concepts_found=True,
        entries=(
            ConceptListEntry(
                handle="speech:fundamental_frequency",
                canonical_name="fundamental_frequency",
                status="accepted",
            ),
        ),
    )


def _search_report() -> ConceptSearchReport:
    return ConceptSearchReport(
        hits=(
            ConceptSearchHit(
                handle="speech:fundamental_frequency",
                logical_id="speech:fundamental_frequency",
                canonical_name="fundamental_frequency",
                definition="Primary oscillation rate.",
                status="accepted",
            ),
        )
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_concept_index_html_route_renders_inventory(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "list_concepts", lambda repo, request: _list_report())

    response = client.get("/concepts?domain=speech")

    assert response.status_code == 200
    html = response.text
    assert html.count("<h1>") == 1
    assert "Concepts" in html
    assert "Concept Inventory" in html
    assert "fundamental_frequency" in html
    assert "/concept/speech%3Afundamental_frequency" in html
    assert "<th scope=\"col\">Status</th>" in html


def test_concept_index_json_route_uses_search_report_when_query_present(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "search_concepts", lambda repo, request: _search_report())

    response = client.get("/concepts.json?q=frequency")

    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"][0]["handle"] == "speech:fundamental_frequency"
    assert payload["hits"][0]["status"] == "accepted"


def test_concept_index_route_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/concepts.json?limit=0")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"


def test_concept_index_search_maps_missing_sidecar_to_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_search(repo: Repository, request) -> ConceptSearchReport:
        raise ConceptSidecarMissingError("sidecar not found. Run 'pks build' first.")

    monkeypatch.setattr(routing, "search_concepts", fake_search)

    response = client.get("/concepts.json?q=frequency")

    assert response.status_code == 409
    assert response.json()["error"]["title"] == "Sidecar Missing"

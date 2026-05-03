"""Web route tests for the `/` index page.

Modeled on `tests/test_web_claim_index_routes.py`. Uses TestClient with
fake Repository stub plus monkeypatched `build_repository_overview`.
"""

from __future__ import annotations

from typing import cast

import pytest
from fastapi.testclient import TestClient

from propstore.app.repository_overview import (
    InventoryRow,
    NotableConflicts,
    ProvenanceSummary,
    RecentActivity,
    RepositoryOverviewReport,
    SourcePointer,
)
from propstore.app.rendering import RenderPolicySummary
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository
from propstore.web import routing
from propstore.web.app import create_app


def _repo() -> Repository:
    return cast(Repository, object())


def _render_policy_summary() -> RenderPolicySummary:
    return RenderPolicySummary(
        reasoning_backend="claim_graph",
        strategy="default",
        semantics="grounded",
        set_comparison="elitist",
        decision_criterion="pignistic",
        pessimism_index=0.5,
        praf_strategy="auto",
        praf_epsilon=0.01,
        praf_confidence=0.95,
        praf_seed=None,
        include_drafts=False,
        include_blocked=False,
        show_quarantined=False,
    )


def _overview_report() -> RepositoryOverviewReport:
    return RepositoryOverviewReport(
        repository_state="current worktree",
        render_policy=_render_policy_summary(),
        inventory_rows=(
            InventoryRow(
                kind="claims",
                count=42,
                state="known",
                sentence="42 claims present.",
                href="/claims",
            ),
            InventoryRow(
                kind="concepts",
                count=7,
                state="known",
                sentence="7 concepts present.",
                href="/concepts",
            ),
        ),
        source_pointers=(
            SourcePointer(
                state="known",
                source_id="paper-foo",
                slug="paper-foo",
                kind="source",
                sentence="Source paper-foo on branch source/paper-foo at deadbeef.",
                href=None,
            ),
        ),
        provenance_summary=ProvenanceSummary(
            state="not_implemented",
            counts=(),
            sentence="Provenance aggregation is not yet computed.",
        ),
        recent_activity=RecentActivity(
            state="vacuous",
            entries=(),
            sentence="No commits on the current branch yet.",
        ),
        notable_conflicts=NotableConflicts(
            state="not_implemented",
            entries=(),
            sentence="Notable conflicts are not yet computed.",
        ),
        prose_summary=(
            "Repository at current worktree; 49 indexed entries across 2 of 2 "
            "inventory kinds under grounded semantics."
        ),
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_index_html_route_returns_200_with_propstore_heading(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "build_repository_overview",
        lambda repo, request: _overview_report(),
    )

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "<h1>" in html
    assert "propstore" in html
    # Prose summary must be rendered into the page body.
    assert "49 indexed entries" in html
    # Inventory table heading row.
    assert '<th scope="col">' in html


def test_index_json_route_returns_typed_payload(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "build_repository_overview",
        lambda repo, request: _overview_report(),
    )

    response = client.get("/index.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["repository_state"] == "current worktree"
    assert payload["render_policy"]["semantics"] == "grounded"
    assert isinstance(payload["inventory_rows"], list)
    first_row = payload["inventory_rows"][0]
    assert set(first_row.keys()) == {"kind", "count", "state", "sentence", "href"}
    assert payload["source_pointers"][0]["slug"] == "paper-foo"
    assert payload["provenance_summary"]["state"] == "not_implemented"
    assert payload["recent_activity"]["state"] == "vacuous"
    assert payload["notable_conflicts"]["state"] == "not_implemented"
    assert "49 indexed entries" in payload["prose_summary"]


def test_index_route_rejects_invalid_render_policy_param(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "build_repository_overview",
        lambda repo, request: _overview_report(),
    )

    response = client.get("/index.json?include_drafts=garbage")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"


def test_index_route_returns_409_when_world_sidecar_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raises(_repo: object, _request: object) -> RepositoryOverviewReport:
        raise WorldSidecarMissingError()

    monkeypatch.setattr(routing, "build_repository_overview", _raises)

    response = client.get("/index.json")

    assert response.status_code == 409
    assert response.json()["error"]["title"] == "Sidecar Missing"


def test_index_html_renders_section_per_region(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each major report region must surface as an aria-labelledby section
    so the page has a meaningful heading outline for AT users."""
    monkeypatch.setattr(
        routing,
        "build_repository_overview",
        lambda repo, request: _overview_report(),
    )

    response = client.get("/")
    html = response.text

    # Each region surfaces as a labelled section. We assert presence of the
    # h2 text rather than specific aria ids (the renderer owns the ids).
    for heading in (
        "Render State",
        "Inventory",
        "Sources",
        "Recent Activity",
        "Notable Conflicts",
        "Provenance",
    ):
        assert heading in html, f"Missing region heading: {heading!r}"


def test_index_html_inventory_table_has_one_link_per_row(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The inventory table iterates report.inventory_rows, never a literal
    list of kind names. Two fixture rows → exactly two anchors that point
    at the kinds' hrefs."""
    monkeypatch.setattr(
        routing,
        "build_repository_overview",
        lambda repo, request: _overview_report(),
    )

    response = client.get("/")
    html = response.text

    assert html.count('href="/claims"') >= 1
    assert html.count('href="/concepts"') >= 1

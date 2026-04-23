from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
import pytest

from propstore.app.claim_views import ClaimViewUnknownClaimError
from propstore.app.neighborhoods import (
    SemanticEdge,
    SemanticFocus,
    SemanticFocusStatus,
    SemanticMove,
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRequest,
    SemanticNeighborhoodRow,
    SemanticNode,
)
from propstore.app.rendering import RenderPolicySummary
from propstore.repository import Repository
from propstore.web import routing
from propstore.web.app import create_app


def _repo() -> Repository:
    return cast(Repository, object())


def _render_policy() -> RenderPolicySummary:
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


def _report() -> SemanticNeighborhoodReport:
    return SemanticNeighborhoodReport(
        focus=SemanticFocus(
            kind="claim",
            focus_id="claim1",
            display_id="Claim One",
            sentence="You are on claim Claim One.",
        ),
        render_policy=_render_policy(),
        status=SemanticFocusStatus(
            state="blocked",
            visible_under_policy=False,
            reason="Focus claim is blocked under the current render policy.",
        ),
        moves=(
            SemanticMove(
                kind="supporters",
                target_count=1,
                state="known",
                sentence="1 claims support this claim.",
                target_ids=("supporter1",),
            ),
            SemanticMove(
                kind="attackers",
                target_count=1,
                state="known",
                sentence="1 claims attack this claim.",
                target_ids=("attacker1",),
            ),
            SemanticMove(
                kind="assumptions",
                target_count=0,
                state="unavailable",
                sentence="Assumption traversal is unavailable in this report.",
            ),
        ),
        nodes=(
            SemanticNode(
                kind="claim",
                node_id="claim1",
                display_id="Claim One",
                sentence="Claim node Claim One.",
            ),
            SemanticNode(
                kind="claim",
                node_id="supporter1",
                display_id="Supporter One",
                sentence="Claim node Supporter One.",
            ),
            SemanticNode(
                kind="claim",
                node_id="attacker1",
                display_id="Attacker One",
                sentence="Claim node Attacker One.",
            ),
        ),
        edges=(
            SemanticEdge(
                source_id="supporter1",
                target_id="claim1",
                edge_kind="supports",
                sentence="Claim Supporter One supports the focus claim Claim One.",
            ),
            SemanticEdge(
                source_id="attacker1",
                target_id="claim1",
                edge_kind="rebuts",
                sentence="Claim Attacker One rebuts the focus claim Claim One.",
            ),
        ),
        table_rows=(
            SemanticNeighborhoodRow(
                section="supporters",
                subject_id="supporter1",
                relation="supports",
                object_id="claim1",
                state="known",
                sentence="Claim supporter1 supports claim claim1.",
            ),
            SemanticNeighborhoodRow(
                section="attackers",
                subject_id="attacker1",
                relation="attacks",
                object_id="claim1",
                state="known",
                sentence="Claim attacker1 attacks claim claim1.",
            ),
            SemanticNeighborhoodRow(
                section="conditions",
                subject_id="claim1",
                relation="has_conditions",
                object_id="vacuous",
                state="vacuous",
                sentence="Claim claim1 has vacuous conditions.",
            ),
            SemanticNeighborhoodRow(
                section="provenance",
                subject_id="claim1",
                relation="has_provenance",
                object_id="unknown",
                state="unknown",
                sentence="Claim claim1 provenance is unknown.",
            ),
            SemanticNeighborhoodRow(
                section="shared_concept",
                subject_id="claim1",
                relation="shares_concept_with",
                object_id="claim2",
                state="known",
                sentence="Claim claim1 shares its concept with claim claim2.",
            ),
            SemanticNeighborhoodRow(
                section="raw_graph_projection",
                subject_id="supporter1",
                relation="supports",
                object_id="claim1",
                state="known",
                sentence="Claim Supporter One supports the focus claim Claim One.",
            ),
        ),
        prose_summary=(
            "Claim Claim One has 1 supporters, 1 attackers, and 1 visible claims "
            "sharing its concept under the current render policy."
        ),
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_neighborhood_html_route_renders_all_report_tables(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[SemanticNeighborhoodRequest] = []

    def fake_build(
        repo: Repository,
        request: SemanticNeighborhoodRequest,
    ) -> SemanticNeighborhoodReport:
        captured.append(request)
        return _report()

    monkeypatch.setattr(routing, "build_semantic_neighborhood", fake_build)

    response = client.get("/claim/claim1/neighborhood?include_blocked=true&limit=12")

    assert response.status_code == 200
    assert captured[0].focus_kind == "claim"
    assert captured[0].focus_id == "claim1"
    assert captured[0].render_policy.include_blocked is True
    assert captured[0].limit == 12
    html = response.text
    assert html.count("<h1>") == 1
    assert "Neighborhood for Claim One" in html
    assert "Available Moves" in html
    assert "Supporters" in html
    assert "Attackers" in html
    assert "Conditions" in html
    assert "Provenance" in html
    assert "Raw Graph Projection" in html
    assert "<th scope=\"col\">Sentence</th>" in html
    assert "Claim Supporter One supports the focus claim Claim One." in html
    assert "unavailable" in html
    assert "vacuous" in html
    assert "/claim/claim1" in html


def test_neighborhood_json_route_uses_same_report(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "build_semantic_neighborhood", lambda repo, request: _report())

    response = client.get("/claim/claim1/neighborhood.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["focus"]["focus_id"] == "claim1"
    assert payload["status"]["state"] == "blocked"
    assert payload["moves"][0]["kind"] == "supporters"
    assert payload["edges"][0]["sentence"] == (
        "Claim Supporter One supports the focus claim Claim One."
    )


def test_neighborhood_route_maps_unknown_claim_to_accessible_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_build(
        repo: Repository,
        request: SemanticNeighborhoodRequest,
    ) -> SemanticNeighborhoodReport:
        raise ClaimViewUnknownClaimError(request.focus_id)

    monkeypatch.setattr(routing, "build_semantic_neighborhood", fake_build)

    html_response = client.get("/claim/missing/neighborhood")
    json_response = client.get("/claim/missing/neighborhood.json")

    assert html_response.status_code == 404
    assert "<h1>Claim Not Found</h1>" in html_response.text
    assert "Claim &#x27;missing&#x27; not found." in html_response.text
    assert json_response.status_code == 404
    assert json_response.json()["error"]["title"] == "Claim Not Found"


def test_neighborhood_route_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/claim/claim1/neighborhood.json?limit=0")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"
    assert response.json()["error"]["message"] == "limit must be between 1 and 500"

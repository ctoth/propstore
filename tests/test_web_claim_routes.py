from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
import pytest

from propstore.app.claim_views import (
    ClaimViewConcept,
    ClaimViewCondition,
    ClaimViewProvenance,
    ClaimViewReport,
    ClaimViewRequest,
    ClaimViewStatus,
    ClaimViewUncertainty,
    ClaimViewUnknownClaimError,
    ClaimViewValue,
)
from propstore.app.rendering import RenderPolicySummary
from propstore.repository import Repository
from propstore.web import routing
from propstore.web.app import create_app


def _repo() -> Repository:
    return cast(Repository, object())


def _report() -> ClaimViewReport:
    return ClaimViewReport(
        claim_id="claim1",
        logical_id=None,
        artifact_id="claim1",
        version_id=None,
        heading="Claim claim1",
        claim_type="mechanism",
        statement=None,
        concept=ClaimViewConcept(
            state="unknown",
            concept_id="concept1",
            canonical_name=None,
            form=None,
        ),
        value=ClaimViewValue(
            state="not_applicable",
            value=None,
            unit=None,
            value_si=None,
            canonical_unit=None,
            sentence="Value is not applicable for mechanism claim.",
        ),
        uncertainty=ClaimViewUncertainty(
            state="missing",
            uncertainty=None,
            uncertainty_type=None,
            lower_bound=None,
            lower_bound_si=None,
            upper_bound=None,
            upper_bound_si=None,
            sample_size=None,
            sentence="Uncertainty is missing.",
        ),
        condition=ClaimViewCondition(
            state="vacuous",
            expression=None,
            sentence="Conditions are vacuous; the claim has no explicit condition filter.",
        ),
        provenance=ClaimViewProvenance(
            state="missing",
            source_slug=None,
            source_id=None,
            source_kind=None,
            paper=None,
            page=None,
            origin_type=None,
            origin_value=None,
            sentence="Provenance is missing.",
        ),
        render_policy=RenderPolicySummary(
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
        ),
        status=ClaimViewStatus(
            state="blocked",
            visible_under_policy=False,
            reason="Claim is blocked under the current render policy.",
            branch="master",
            build_status="ingested",
            stage="accepted",
            promotion_status="accepted",
        ),
        repository_state="current worktree",
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_claim_html_route_renders_accessible_literals(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[ClaimViewRequest] = []

    def fake_build(repo: Repository, request: ClaimViewRequest) -> ClaimViewReport:
        captured.append(request)
        return _report()

    monkeypatch.setattr(routing, "build_claim_view", fake_build)

    response = client.get("/claim/claim1?include_drafts=true")

    assert response.status_code == 200
    assert captured[0].claim_id == "claim1"
    assert captured[0].render_policy.include_drafts is True
    html = response.text
    assert html.count("<h1>") == 1
    assert "<main>" in html
    assert "unknown" in html
    assert "vacuous" in html
    assert "missing" in html
    assert "not applicable" in html
    assert "blocked" in html
    assert "/claim/claim1/neighborhood" in html


def test_claim_json_route_uses_same_report(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "build_claim_view", lambda repo, request: _report())

    response = client.get("/claim/claim1.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_id"] == "claim1"
    assert payload["concept"]["state"] == "unknown"
    assert payload["value"]["state"] == "not_applicable"
    assert payload["condition"]["state"] == "vacuous"
    assert payload["status"]["state"] == "blocked"


def test_claim_route_maps_unknown_claim_to_accessible_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_build(repo: Repository, request: ClaimViewRequest) -> ClaimViewReport:
        raise ClaimViewUnknownClaimError(request.claim_id)

    monkeypatch.setattr(routing, "build_claim_view", fake_build)

    html_response = client.get("/claim/missing")
    json_response = client.get("/claim/missing.json")

    assert html_response.status_code == 404
    assert "<h1>Claim Not Found</h1>" in html_response.text
    assert "Claim &#x27;missing&#x27; not found." in html_response.text
    assert json_response.status_code == 404
    assert json_response.json()["error"]["title"] == "Claim Not Found"


def test_claim_route_rejects_invalid_policy_query(
    client: TestClient,
) -> None:
    response = client.get("/claim/claim1.json?include_drafts=maybe")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"

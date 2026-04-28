from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient
import pytest

from propstore.app.concept_views import (
    ConceptClaimEntry,
    ConceptClaimGroup,
    ConceptProvenanceSummary,
    ConceptRelatedClaimLink,
    ConceptUncertaintySummary,
    ConceptValueSummary,
    ConceptViewForm,
    ConceptViewReport,
    ConceptViewRequest,
    ConceptViewStatus,
    ConceptViewUnknownConceptError,
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


def _report() -> ConceptViewReport:
    return ConceptViewReport(
        concept_id="concept1",
        logical_id="speech:fundamental_frequency",
        artifact_id="ps:concept:fundamental_frequency",
        version_id="concept-version-1",
        heading="Concept fundamental_frequency",
        canonical_name="fundamental_frequency",
        definition="Primary oscillation rate.",
        domain="speech",
        kind_type="quantity",
        form=ConceptViewForm(
            state="known",
            form_name="frequency",
            unit="Hz",
            range_text="75.0 to 300.0",
            sentence="Concept form is frequency with visible unit Hz.",
        ),
        status=ConceptViewStatus(
            state="blocked",
            concept_status="accepted",
            visible_claim_count=1,
            blocked_claim_count=1,
            total_claim_count=2,
            reason="Some claims for this concept are blocked under the current render policy.",
        ),
        render_policy=_render_policy(),
        repository_state="current worktree",
        claim_groups=(
            ConceptClaimGroup(
                claim_type="measurement",
                visible_count=1,
                blocked_count=1,
                entries=(
                    ConceptClaimEntry(
                        claim_id="claim1",
                        logical_id="paper:claim1",
                        claim_type="measurement",
                        value_display="100 Hz",
                        condition_display="vacuous",
                        status_state="known",
                        status_reason="Claim is visible under the current render policy.",
                    ),
                ),
                sentence="1 visible measurement claims and 1 blocked claims refer to this concept.",
            ),
        ),
        value_summary=ConceptValueSummary(
            state="known",
            claim_count=1,
            unit="Hz",
            sentence="1 visible claims provide values in Hz.",
        ),
        uncertainty_summary=ConceptUncertaintySummary(
            state="missing",
            claim_count=0,
            sentence="Visible claims do not provide uncertainty information.",
        ),
        provenance_summary=ConceptProvenanceSummary(
            state="known",
            claim_count=1,
            source_count=1,
            papers=("paper1",),
            sentence="1 visible claims provide provenance across 1 sources.",
        ),
        related_claim_links=(
            ConceptRelatedClaimLink(
                claim_id="claim1",
                logical_id="paper:claim1",
                relation="instantiates",
                sentence="Claim paper:claim1 instantiates this concept.",
            ),
        ),
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routing.Repository, "find", lambda start: _repo())
    return TestClient(create_app())


def test_concept_html_route_renders_accessible_literals(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[ConceptViewRequest] = []

    def fake_build(repo: Repository, request: ConceptViewRequest) -> ConceptViewReport:
        captured.append(request)
        return _report()

    monkeypatch.setattr(routing, "build_concept_view", fake_build)

    response = client.get("/concept/speech%3Afundamental_frequency?include_drafts=true")

    assert response.status_code == 200
    assert captured[0].concept_id_or_name == "speech:fundamental_frequency"
    assert captured[0].render_policy.include_drafts is True
    html = response.text
    assert html.count("<h1>") == 1
    assert "<main>" in html
    assert "Concept fundamental_frequency" in html
    assert "blocked" in html
    assert "known" in html
    assert "missing" in html
    assert "/claim/claim1" in html
    assert "<th scope=\"col\">Claim</th>" in html


def test_concept_json_route_uses_same_report(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routing, "build_concept_view", lambda repo, request: _report())

    response = client.get("/concept/speech%3Afundamental_frequency.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["concept_id"] == "concept1"
    assert payload["status"]["state"] == "blocked"
    assert payload["form"]["state"] == "known"
    assert payload["uncertainty_summary"]["state"] == "missing"


def test_concept_route_maps_unknown_concept_to_accessible_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_build(repo: Repository, request: ConceptViewRequest) -> ConceptViewReport:
        raise ConceptViewUnknownConceptError(request.concept_id_or_name)

    monkeypatch.setattr(routing, "build_concept_view", fake_build)

    html_response = client.get("/concept/missing")
    json_response = client.get("/concept/missing.json")

    assert html_response.status_code == 404
    assert "<h1 id=\"error-heading\">Concept Not Found</h1>" in html_response.text
    assert "Concept &#x27;missing&#x27; not found." in html_response.text
    assert json_response.status_code == 404
    assert json_response.json()["error"]["title"] == "Concept Not Found"


def test_concept_route_rejects_invalid_policy_query(client: TestClient) -> None:
    response = client.get("/concept/concept1.json?include_drafts=maybe")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Invalid Request"


def test_concept_route_rejects_unsupported_repository_view(client: TestClient) -> None:
    response = client.get("/concept/concept1.json?branch=feature")

    assert response.status_code == 400
    assert response.json()["error"]["title"] == "Unsupported Repository State"
    assert response.json()["error"]["message"] == "branch-qualified views are not implemented"

from __future__ import annotations

from pathlib import Path

from propstore.app.claim_views import ClaimViewRequest, build_claim_view
from propstore.app.concept_views import ConceptViewRequest, build_concept_view
from propstore.app.neighborhoods import (
    SemanticNeighborhoodRequest,
    build_semantic_neighborhood,
)
from tests.web_demo_fixture import seed_web_demo_repository


def test_web_demo_fixture_exercises_first_surface_states(tmp_path: Path) -> None:
    fixture = seed_web_demo_repository(tmp_path)

    claim_report = build_claim_view(
        fixture.repo,
        ClaimViewRequest(claim_id=fixture.focus_claim_id),
    )
    concept_report = build_concept_view(
        fixture.repo,
        ConceptViewRequest(concept_id_or_name=fixture.concept_id),
    )
    neighborhood_report = build_semantic_neighborhood(
        fixture.repo,
        SemanticNeighborhoodRequest(
            focus_kind="claim",
            focus_id=fixture.focus_claim_id,
        ),
    )

    assert claim_report.claim_id == fixture.focus_claim_id
    assert claim_report.concept.state == "known"
    assert claim_report.concept.concept_id == fixture.concept_id
    assert claim_report.uncertainty.state == "known"
    assert claim_report.uncertainty.uncertainty == 0.25
    assert claim_report.provenance.state == "known"
    assert claim_report.provenance.paper == "demo_source"
    assert claim_report.provenance.page == 7
    assert claim_report.status.state == "blocked"
    assert claim_report.status.visible_under_policy is False

    assert concept_report.concept_id == fixture.concept_id
    assert concept_report.status.state == "known"
    assert concept_report.status.visible_claim_count == 2
    assert concept_report.status.blocked_claim_count == 1
    assert {group.claim_type for group in concept_report.claim_groups} == {
        "measurement",
        "parameter",
    }
    assert concept_report.value_summary.state == "known"
    assert concept_report.uncertainty_summary.state == "known"
    assert concept_report.provenance_summary.state == "known"
    assert concept_report.provenance_summary.papers == ("demo_source",)
    assert len(concept_report.related_claim_links) == 2

    moves = {move.kind: move for move in neighborhood_report.moves}
    assert moves["supporters"].target_ids == (fixture.supporter_claim_id,)
    assert moves["attackers"].target_ids == (fixture.attacker_claim_id,)
    assert neighborhood_report.status.state == "blocked"
    assert any(edge.edge_kind == "supports" for edge in neighborhood_report.edges)
    assert any(edge.edge_kind == "rebuts" for edge in neighborhood_report.edges)

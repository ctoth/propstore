"""Phase 10-2: semantic-neighborhood routes (claim focus only)."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_neighborhood_json_reports_moves_and_edges(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/claim/p_speed/neighborhood.json").json()

    assert payload["focus"]["focus_id"] == "p_speed"
    move_kinds = {move["kind"] for move in payload["moves"]}
    assert {"supporters", "attackers", "shared_concept"} <= move_kinds
    edge_kinds = {edge["edge_kind"] for edge in payload["edges"]}
    assert {"supports", "rebuts"} <= edge_kinds


def test_neighborhood_html_has_section_tables(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/claim/p_speed/neighborhood").text

    assert "Neighborhood for" in html
    for heading in (
        "Supporters",
        "Attackers",
        "Shared Concept",
        "Raw Graph Projection",
    ):
        assert heading in html
    assert "Open claim view for this focus claim" in html
    assert 'href="/claim/p_speed"' in html


def test_neighborhood_unknown_claim_is_404(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claim/nope/neighborhood.json")

    assert response.status_code == 404


def test_neighborhood_blocked_claim_is_404(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claim/p_blocked/neighborhood.json")

    assert response.status_code == 404

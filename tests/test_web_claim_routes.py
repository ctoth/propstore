"""Phase 10-2: single-claim view routes (JSON + HTML) and their honest errors."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_claim_json_renders_per_field_view(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/claim/p_speed.json").json()

    assert payload["claim_id"] == "p_speed"
    assert payload["claim_type"] == "parameter"
    assert payload["value"]["state"] == "known"
    assert payload["concept"]["concept_id"] == "speed"
    assert "render_policy" in payload


def test_claim_html_has_summary_and_neighborhood_link(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/claim/p_speed").text

    assert "<h1" in html
    assert "Claim p_speed" in html
    assert "Open semantic neighborhood for this claim" in html
    assert 'href="/claim/p_speed/neighborhood"' in html


def test_unknown_claim_is_404_not_collapsed(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claim/does-not-exist.json")

    assert response.status_code == 404
    assert response.json()["error"]["title"] == "Claim Not Found"


def test_blocked_claim_is_hidden_as_404(tmp_path: Path) -> None:
    # p_blocked exists in storage but is BLOCKED; the default policy hides it.
    response = demo_client(tmp_path).get("/claim/p_blocked")

    assert response.status_code == 404


def test_blocked_claim_visible_when_policy_includes_blocked(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claim/p_blocked.json?include_blocked=true")

    assert response.status_code == 200
    assert response.json()["claim_id"] == "p_blocked"

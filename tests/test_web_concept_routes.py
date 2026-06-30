"""Phase 10-2: single-concept view routes (JSON + HTML)."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_concept_json_renders_view(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/concept/speed.json").json()

    assert payload["concept_id"] == "speed"
    assert payload["canonical_name"] == "Speed"
    assert "claim_groups" in payload
    assert "render_policy" in payload


def test_concept_html_has_section_landmarks(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/concept/speed").text

    assert "<h1" in html
    assert "Concept Speed" in html
    assert "Claims By Type" in html
    assert "Related Claims" in html


def test_unknown_concept_is_404(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/concept/nonexistent.json")

    assert response.status_code == 404
    assert response.json()["error"]["title"] == "Concept Not Found"

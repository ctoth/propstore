"""Phase 10-2: the repository-overview index route (JSON + HTML)."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_index_json_reports_inventory_and_policy(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/index.json").json()

    assert "inventory_rows" in payload
    assert "render_policy" in payload
    kinds = {row["kind"] for row in payload["inventory_rows"]}
    assert {"concepts", "claims"} <= kinds
    concepts_row = next(
        row for row in payload["inventory_rows"] if row["kind"] == "concepts"
    )
    assert concepts_row["count"] >= 1


def test_index_html_has_overview_landmarks(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/").text

    assert "<h1" in html
    assert "propstore" in html
    assert "Inventory" in html
    assert 'href="/concepts"' in html
    assert 'href="/claims"' in html


def test_index_json_rejects_invalid_render_policy(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/index.json?strategy=not-a-strategy")

    assert response.status_code == 400
    assert response.json()["error"]["status_code"] == 400

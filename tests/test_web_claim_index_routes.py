"""Phase 10-2: claim list/search index routes."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_claims_json_lists_visible_claims(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/claims.json").json()

    ids = {entry["claim_id"] for entry in payload["entries"]}
    assert "p_speed" in ids
    # DRAFT and BLOCKED claims are hidden under the default policy.
    assert "p_draft" not in ids
    assert "p_blocked" not in ids


def test_claims_json_scopes_to_concept(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/claims.json?concept=speed").json()

    ids = {entry["claim_id"] for entry in payload["entries"]}
    assert "p_speed" in ids
    assert "p_missingval" not in ids  # p_missingval is about distance


def test_claims_json_search_matches_query(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/claims.json?q=friction").json()

    ids = {entry["claim_id"] for entry in payload["entries"]}
    assert "mech1" in ids


def test_claims_html_links_each_claim(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/claims").text

    assert ">p_speed</a>" in html
    assert 'href="/claim/p_speed"' in html


def test_claims_json_rejects_out_of_range_limit(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claims.json?limit=0")

    assert response.status_code == 400
    assert "limit" in response.json()["error"]["message"]

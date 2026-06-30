"""Phase 10-2: concept list/search index routes."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_concepts_json_lists_visible_concepts(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/concepts.json").json()

    assert payload["concepts_found"] is True
    ids = {entry["concept_id"] for entry in payload["entries"]}
    assert {"speed", "distance"} <= ids
    # The DRAFT concept is hidden under the default policy.
    assert "draftconcept" not in ids


def test_concepts_json_search_returns_hits(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/concepts.json?q=speed").json()

    ids = {hit["concept_id"] for hit in payload["hits"]}
    assert "speed" in ids


def test_concepts_html_links_each_concept(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/concepts").text

    assert 'href="/concept/speed"' in html
    assert ">speed</a>" in html

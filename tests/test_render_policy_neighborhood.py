from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from propstore.web.app import create_app
from tests.web_demo_fixture import seed_web_demo_repository


def test_neighborhood_hides_blocked_stance_endpoints(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    with sqlite3.connect(fixture.repo.sidecar_path) as conn:
        conn.execute(
            """
            INSERT INTO relation_edge (
                source_kind, source_id, relation_type, target_kind, target_id,
                confidence, opinion_belief, opinion_disbelief,
                opinion_uncertainty, opinion_base_rate
            ) VALUES ('claim', ?, 'supports', 'claim', ?, 0.9, 0.7, 0.1, 0.2, 0.5)
            """,
            (fixture.focus_claim_id, fixture.supporter_claim_id),
        )

    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.supporter_claim_id}/neighborhood.json")

    assert response.status_code == 200
    payload = response.json()
    serialized = response.text
    assert fixture.focus_claim_id not in serialized
    assert all(fixture.focus_claim_id not in move["target_ids"] for move in payload["moves"])
    assert all(node["node_id"] != fixture.focus_claim_id for node in payload["nodes"])
    assert all(edge["source_id"] != fixture.focus_claim_id for edge in payload["edges"])
    assert all(edge["target_id"] != fixture.focus_claim_id for edge in payload["edges"])
    assert "0 supporters" in payload["prose_summary"]


def test_blocked_focus_claim_neighborhood_is_not_rendered(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.focus_claim_id}/neighborhood.json")

    assert response.status_code == 404
    assert response.json()["error"]["title"] == "Not Found"
    assert fixture.focus_claim_id not in response.text

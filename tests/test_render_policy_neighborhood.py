from __future__ import annotations

import sqlite3

import msgspec
from fastapi.testclient import TestClient

from propstore.opinion import Opinion
from propstore.web.app import create_app
from tests.web_demo_fixture import seed_web_demo_repository


def test_blocked_focus_claim_neighborhood_is_not_rendered(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.focus_claim_id}/neighborhood.json")

    assert response.status_code == 404
    assert response.json()["error"]["title"] == "Not Found"
    assert fixture.focus_claim_id not in response.text

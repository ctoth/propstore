from __future__ import annotations

from fastapi.testclient import TestClient

from propstore.web.app import create_app
from tests.web_demo_fixture import seed_web_demo_repository


def test_concept_default_policy_html_does_not_mention_hidden_counts(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/concept/{fixture.concept_id}")

    assert response.status_code == 200
    html = response.text
    assert fixture.focus_claim_id not in html
    assert "blocked claims" not in html

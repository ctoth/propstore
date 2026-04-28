from __future__ import annotations

from fastapi.testclient import TestClient

from propstore.web.app import create_app
from tests.web_demo_fixture import seed_web_demo_repository


def test_blocked_claim_json_is_not_rendered(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.focus_claim_id}.json")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "title": "Not Found",
            "message": "Not Found",
            "status_code": 404,
        }
    }
    body = response.text
    assert fixture.focus_claim_id not in body
    assert "295" not in body
    assert "statement" not in body
    assert "value" not in body
    assert "provenance" not in body


def test_blocked_claim_html_is_accessible_error_not_redacted_page(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.focus_claim_id}")

    assert response.status_code == 404
    html = response.text
    assert "<title>Not Found - propstore</title>" in html
    assert html.count("<h1") == 1
    assert "<h1 id=\"error-heading\">Not Found</h1>" in html
    assert "<main aria-labelledby=\"error-heading\">" in html
    assert "/claims" in html
    assert "/concepts" in html
    assert fixture.focus_claim_id not in html
    assert "295" not in html
    assert "redacted" not in html.casefold()
    assert "redaction" not in html.casefold()


def test_visible_claim_still_renders(tmp_path) -> None:
    fixture = seed_web_demo_repository(tmp_path)
    client = TestClient(create_app(repository_root=fixture.repo.root))

    response = client.get(f"/claim/{fixture.supporter_claim_id}.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_id"] == fixture.supporter_claim_id
    assert payload["status"]["visible_under_policy"] is True

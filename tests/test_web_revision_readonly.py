"""Phase 10-2: the read-only revision view over support_revision workflows."""

from __future__ import annotations

from pathlib import Path

from tests.web_helpers import demo_client


def test_revision_base_route_reports_base_and_entrenchment(tmp_path: Path) -> None:
    payload = demo_client(tmp_path).get("/world/revision/base.json").json()

    assert "base" in payload
    assert "entrenchment" in payload
    # The belief base lowers to a JSON object; the route never fabricates content.
    assert isinstance(payload["base"], dict)
    assert isinstance(payload["entrenchment"], dict)


def test_revision_base_route_is_read_only_get(tmp_path: Path) -> None:
    response = demo_client(tmp_path).post("/world/revision/base.json")

    assert response.status_code == 405

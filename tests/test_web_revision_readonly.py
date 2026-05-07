from __future__ import annotations

from fastapi.testclient import TestClient

from propstore.web.app import create_app
from tests.test_revision_phase1_cli import revision_cli_workspace


def test_web_revision_base_route_is_read_only_app_backed(revision_cli_workspace) -> None:
    client = TestClient(create_app(repository_root=revision_cli_workspace))

    response = client.get(
        "/world/revision/base.json",
        params={"context": "ctx_test", "speaker_sex": "male"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["base"]["atoms"]
    assert payload["entrenchment"]["ranked_atom_ids"]
    assert "rev" not in payload

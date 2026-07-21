"""Phase 10-3: embedding-backed similarity web routes (JSON).

Skip-gated on the ``sqlite-vec`` extra. Embeds the demo corpus through a
deterministic fake embedder, then drives the read-only web app's
``/claim/{id}/similar.json`` and ``/concept/{id}/similar.json`` routes. Without an
index the route returns an honest empty hit list rather than a fabricated one.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlite_vec")

from tests.app_render_helpers import build_demo_repo  # noqa: E402
from propstore.families.embeddings.declaration import (  # noqa: E402
    embed_claims_at,
    embed_concepts_at,
)
from propstore.repository import Repository  # noqa: E402
from propstore.web.app import create_app  # noqa: E402
from propstore.world import WorldQuery  # noqa: E402


def _fake_litellm() -> MagicMock:
    litellm = MagicMock()

    def embedding(model: str, input: Sequence[str]) -> MagicMock:
        response = MagicMock()
        response.data = [
            {"embedding": [float(len(text)), float(sum(map(ord, text)) % 97)]}
            for text in input
        ]
        return response

    litellm.embedding.side_effect = embedding
    return litellm


def _embed_demo(repo: Repository) -> None:
    with WorldQuery(repo) as world:
        claims = list(world.claims_for(None))
        concepts = list(world.all_concepts())
        path = world.sidecar_path
    with patch(
        "propstore.heuristic.embed.require_litellm", return_value=_fake_litellm()
    ):
        embed_claims_at(path, claims, "fake/model")
        embed_concepts_at(path, concepts, "fake/model")


def test_claim_similar_route_returns_hits(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    _embed_demo(repo)
    client = TestClient(create_app(repository_root=repo.root))

    payload = client.get("/claim/p_speed/similar.json?model=fake/model").json()
    assert payload["claim_id"] == "p_speed"
    assert payload["model"] == "fake/model"
    hit_ids = {hit["claim_id"] for hit in payload["hits"]}
    assert "p_speed" not in hit_ids  # self excluded
    assert hit_ids  # neighbours found
    assert all(hit["distance"] >= 0.0 for hit in payload["hits"])


def test_concept_similar_route_returns_hits(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    _embed_demo(repo)
    client = TestClient(create_app(repository_root=repo.root))

    payload = client.get("/concept/speed/similar.json?model=fake/model").json()
    assert payload["concept_id"] == "speed"
    hit_ids = {hit["concept_id"] for hit in payload["hits"]}
    assert "speed" not in hit_ids
    assert hit_ids


def test_similar_route_honest_empty_without_index(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    client = TestClient(create_app(repository_root=repo.root))

    payload = client.get("/claim/p_speed/similar.json").json()
    assert payload["hits"] == []

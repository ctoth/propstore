from __future__ import annotations

from pathlib import Path

import propstore.app.concepts.display as concepts_display_mod
import propstore.app.concepts.embedding as concepts_embedding_mod
from propstore.app.concepts import (
    ConceptEmbedRequest,
    ConceptSearchRequest,
    ConceptSimilarRequest,
    embed_concept_embeddings,
    find_similar_concepts,
    search_concepts,
)
from propstore.repository import Repository
from tests.family_helpers import materialized_world_store_path


def _repo_with_sidecar(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    materialized_world_store_path(repo, force=True)
    return repo


def test_search_concepts_uses_concept_declaration_query_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    calls: list[tuple[str, int]] = []

    def fake_search(sidecar, *, query, limit):
        assert sidecar.exists()
        calls.append((query, limit))
        return [
            {
                "handle": "concept-a",
                "logical_id": "speech:concept-a",
                "canonical_name": "concept a",
                "status": "accepted",
                "definition": "definition text",
            }
        ]

    monkeypatch.setattr(
        concepts_display_mod,
        "fetch_concept_search_hits_from_sidecar",
        fake_search,
    )

    report = search_concepts(repo, ConceptSearchRequest(query="concept", limit=7))

    assert calls == [("concept", 7)]
    assert report.hits[0].handle == "concept-a"
    assert report.hits[0].logical_id == "speech:concept-a"
    assert report.hits[0].canonical_name == "concept a"
    assert report.hits[0].status == "accepted"


def test_embed_concept_embeddings_uses_concept_declaration_embedding_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    calls: list[tuple[str, int]] = []

    def fake_embed_for_request(
        sidecar,
        *,
        concept_id,
        embed_all,
        model,
        batch_size,
        on_progress,
    ):
        assert sidecar.exists()
        assert concept_id is None
        assert embed_all is True
        calls.append((model, batch_size))
        if on_progress is not None:
            on_progress(model, 4, 8)
        return [(model, {"embedded": 4, "skipped": 2, "errors": 0})]

    monkeypatch.setattr(
        concepts_embedding_mod,
        "embed_concepts_for_request",
        fake_embed_for_request,
    )
    progress: list[tuple[str, int, int]] = []

    report = embed_concept_embeddings(
        repo,
        ConceptEmbedRequest(
            concept_id=None,
            embed_all=True,
            model="model-a",
            batch_size=13,
        ),
        on_progress=lambda model_name, done, total: progress.append(
            (model_name, done, total)
        ),
    )

    assert calls == [("model-a", 13)]
    assert progress == [("model-a", 4, 8)]
    assert report.results[0].embedded == 4
    assert report.results[0].skipped == 2


def test_find_similar_concepts_resolves_id_uses_default_model_and_closes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    captured: dict[str, object] = {}

    def fake_find_similar_rows(
        sidecar,
        *,
        concept_id,
        model,
        top_k,
        agree,
        disagree,
    ):
        captured.update(
            {
                "sidecar_exists": sidecar.exists(),
                "concept_id": concept_id,
                "model_name": model,
                "top_k": top_k,
                "agree": agree,
                "disagree": disagree,
            }
        )
        return [
            {
                "distance": 0.25,
                "primary_logical_id": "concept-b",
                "canonical_name": "concept b",
                "definition": "neighbor definition",
            }
        ]

    monkeypatch.setattr(
        concepts_embedding_mod,
        "find_similar_concept_rows",
        fake_find_similar_rows,
    )

    report = find_similar_concepts(
        repo,
        ConceptSimilarRequest(
            concept_id="concept-a",
            model=None,
            top_k=6,
        ),
    )

    assert captured == {
        "sidecar_exists": True,
        "concept_id": "concept-a",
        "model_name": None,
        "top_k": 6,
        "agree": False,
        "disagree": False,
    }
    assert report.hits[0].concept_id == "concept-b"
    assert report.hits[0].canonical_name == "concept b"

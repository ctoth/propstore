from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import propstore.app.concepts as concepts_mod
import propstore.app.concepts.display as concepts_display_mod
import propstore.app.concepts.embedding as concepts_embedding_mod
import propstore.embed as embed_mod
from propstore.app.concepts import (
    ConceptEmbedRequest,
    ConceptSearchRequest,
    ConceptSimilarRequest,
    embed_concept_embeddings,
    find_similar_concepts,
    search_concepts,
)
from propstore.repository import Repository


def _repo_with_sidecar(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    repo.sidecar_path.touch()
    return repo


def test_search_concepts_owns_sidecar_query_and_connection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [("concept-a", "concept a", "definition text")]
    conn.execute.return_value = cursor

    monkeypatch.setattr(concepts_display_mod, "connect_sidecar", lambda path: conn)

    report = search_concepts(repo, ConceptSearchRequest(query="concept", limit=7))

    conn.execute.assert_called_once()
    assert conn.execute.call_args.args[1] == ("concept", 7)
    assert report.hits[0].logical_id == "concept-a"
    assert report.hits[0].canonical_name == "concept a"
    conn.close.assert_called_once()


def test_embed_concept_embeddings_owns_connection_and_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    conn = MagicMock()
    calls: list[tuple[str, int]] = []

    def fake_embed_concepts(
        conn_arg,
        model_name,
        *,
        concept_ids,
        batch_size,
        on_progress,
    ):
        assert conn_arg is conn
        assert concept_ids is None
        calls.append((model_name, batch_size))
        if on_progress is not None:
            on_progress(4, 8)
        return {"embedded": 4, "skipped": 2, "errors": 0}

    monkeypatch.setattr(concepts_embedding_mod, "connect_sidecar", lambda path: conn)
    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn_arg: None)
    monkeypatch.setattr(embed_mod, "embed_concepts", fake_embed_concepts)
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
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


def test_find_similar_concepts_resolves_id_uses_default_model_and_closes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    conn = MagicMock()
    captured: dict[str, object] = {}

    class Cursor:
        def __init__(self, row):
            self._row = row

        def fetchone(self):
            return self._row

    def fake_execute(sql, params):
        assert params == ("concept-a",)
        return Cursor({"id": "internal-a"})

    def fake_find_similar(conn_arg, concept_id, model_name, *, top_k):
        captured.update(
            {
                "conn": conn_arg,
                "concept_id": concept_id,
                "model_name": model_name,
                "top_k": top_k,
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

    conn.execute.side_effect = fake_execute
    monkeypatch.setattr(concepts_embedding_mod, "connect_sidecar", lambda path: conn)
    monkeypatch.setattr(embed_mod, "_load_vec_extension", lambda conn_arg: None)
    monkeypatch.setattr(
        embed_mod,
        "get_registered_models",
        lambda conn_arg: [{"model_name": "model-a"}],
    )
    monkeypatch.setattr(embed_mod, "find_similar_concepts", fake_find_similar)

    report = find_similar_concepts(
        repo,
        ConceptSimilarRequest(
            concept_id="concept-a",
            model=None,
            top_k=6,
        ),
    )

    assert captured == {
        "conn": conn,
        "concept_id": "internal-a",
        "model_name": "model-a",
        "top_k": 6,
    }
    assert report.hits[0].concept_id == "concept-b"
    assert report.hits[0].canonical_name == "concept b"
    conn.close.assert_called_once()

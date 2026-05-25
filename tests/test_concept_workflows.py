from __future__ import annotations

from pathlib import Path

import propstore.app.concepts.display as concepts_display_mod
import propstore.app.concepts.embedding as concepts_embedding_mod
from quire.derived_store import DerivedStoreHandle
from quire.sqlalchemy_store import create_sqlalchemy_store
from sqlalchemy import select
from propstore.core.store_results import ConceptSimilarityHit
from propstore.families.concepts.declaration import CONCEPT_CHARTER
from propstore.families.registry import world_schema
from propstore.app.concepts import (
    ConceptEmbedRequest,
    ConceptSearchRequest,
    ConceptSimilarRequest,
    embed_concept_embeddings,
    find_similar_concepts,
    search_concepts,
)
from propstore.repository import Repository
from propstore.world import WorldQuery
from tests.family_helpers import materialized_world_store_path


def _repo_with_sidecar(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    materialized_world_store_path(repo, force=True)
    return repo


def test_search_concepts_uses_quire_fts_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    calls: list[tuple[str, int]] = []
    schema = world_schema()
    concept_model = schema.model(CONCEPT_CHARTER.family.name)
    store_path = tmp_path / "search-sidecar.sqlite"
    create_sqlalchemy_store(store_path, schema)
    handle = DerivedStoreHandle(
        projection_id="propstore.world.test",
        source_commit="test",
        content_hash="test",
        cache_key="test",
        path=store_path,
    )
    with handle.writable_session(schema) as derived:
        derived.add(
            schema.construct(
                "concept",
                {
                    "id": "ps:concept:test",
                    "canonical_name": "concept a",
                    "primary_logical_id": "speech:concept-a",
                    "logical_ids_json": "[]",
                    "version_id": "",
                    "status": "accepted",
                    "definition": "definition text",
                    "content_hash": "hash-concept-a",
                    "seq": 1,
                    "kind_type": "quantity",
                    "form": "scalar",
                },
            )
        )
        derived.commit()
    with handle.readonly_session(schema) as derived:
        concept = derived.execute(select(concept_model)).scalars().one()

    class FakeHit:
        entity_id = str(concept.id)

    def fake_search(derived, index_name, query, *, limit=None):
        calls.append((query, int(limit or 0)))
        assert index_name == "concept_fts"
        return (FakeHit(),)

    monkeypatch.setattr(
        concepts_display_mod,
        "search_fts_index",
        fake_search,
    )
    monkeypatch.setattr(
        concepts_display_mod,
        "build_repository_world_store",
        lambda repo: (handle, False),
    )

    report = search_concepts(repo, ConceptSearchRequest(query="concept", limit=7))

    assert calls == [("concept", 7)]
    assert report.hits[0].handle == str(concept.primary_logical_id or concept.id)
    assert report.hits[0].canonical_name == str(concept.canonical_name)


def test_embed_concept_embeddings_uses_concept_declaration_embedding_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = _repo_with_sidecar(tmp_path)
    calls: list[tuple[str, int]] = []

    def fake_embed_for_request(
        derived_store,
        *,
        concept_id,
        embed_all,
        model,
        batch_size,
        on_progress,
    ):
        assert derived_store.path.exists()
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

    def fake_similar_concepts(
        self,
        concept_id,
        model_name=None,
        top_k=10,
    ):
        captured.update(
            {
                "sidecar_exists": self._derived_store.path.exists(),
                "concept_id": concept_id,
                "model_name": model_name,
                "top_k": top_k,
            }
        )
        return [
            ConceptSimilarityHit(
                distance=0.25,
                concept_id="ps:concept:b",
                primary_logical_id="concept-b",
                canonical_name="concept b",
                definition="neighbor definition",
            )
        ]

    monkeypatch.setattr(WorldQuery, "similar_concepts", fake_similar_concepts)

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
    }
    assert report.hits[0].concept_id == "concept-b"
    assert report.hits[0].canonical_name == "concept b"

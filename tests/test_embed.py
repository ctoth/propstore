"""Generic embedding layer — store-protocol embed, no silent error swallowing.

Rewrite-native port of the reference ``test_embed_operational_error.py``: drives
``embed_entities`` against an in-memory store with a patched ``require_litellm``,
so it needs neither the ``litellm`` nor ``sqlite-vec`` extra. The load-bearing
behaviour: an unchanged content hash is skipped, a transient API error counts as a
batch error, and an *unexpected* error (storage ``OperationalError`` or provider
``RuntimeError``) propagates rather than being silently swallowed.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from unittest.mock import MagicMock, patch

import pytest

from propstore.core.embeddings import EmbeddingEntity
from propstore.heuristic.embed import deserialize_float32, embed_entities, serialize_float32
from propstore.heuristic.embedding_identity import EmbeddingModelIdentity


class _MemoryStore:
    def __init__(self, entities: list[EmbeddingEntity], existing: dict[str, str] | None = None):
        self._entities = entities
        self._existing = existing or {}
        self.prepared: tuple[EmbeddingModelIdentity, int, str] | None = None
        self.saved: list[tuple[EmbeddingModelIdentity, EmbeddingEntity, bytes, str]] = []

    def ensure_storage(self) -> None:
        pass

    def load_entities(
        self, entity_ids: Sequence[str] | None = None
    ) -> list[EmbeddingEntity]:
        if entity_ids is None:
            return self._entities
        wanted = set(entity_ids)
        return [entity for entity in self._entities if entity.entity_id in wanted]

    def existing_content_hashes(
        self, model_identity: EmbeddingModelIdentity
    ) -> Mapping[str, str]:
        return self._existing

    def prepare_model(
        self, model_identity: EmbeddingModelIdentity, dimensions: int, created_at: str
    ) -> None:
        self.prepared = (model_identity, dimensions, created_at)

    def save_embedding(
        self,
        model_identity: EmbeddingModelIdentity,
        entity: EmbeddingEntity,
        vector_blob: bytes,
        embedded_at: str,
    ) -> None:
        self.saved.append((model_identity, entity, vector_blob, embedded_at))


def _litellm_returning(vectors: list[list[float]]) -> MagicMock:
    litellm = MagicMock()
    litellm.embedding.return_value.data = [{"embedding": vector} for vector in vectors]
    return litellm


def test_float32_round_trip() -> None:
    assert deserialize_float32(serialize_float32([1.0, 2.0, 3.0])) == [1.0, 2.0, 3.0]


def test_embeds_entity_and_prepares_model() -> None:
    store = _MemoryStore([EmbeddingEntity("c1", 7, "h1", "claim summary")])
    litellm = _litellm_returning([[1.0, 2.0]])
    with patch("propstore.heuristic.embed.require_litellm", return_value=litellm):
        result = embed_entities(store, "provider/model", entity_ids=["c1"])

    assert result == {"embedded": 1, "skipped": 0, "errors": 0}
    assert store.prepared is not None
    identity, dimensions, _created = store.prepared
    assert identity.provider == "litellm"
    assert identity.model_name == "provider/model"
    assert dimensions == 2
    assert len(store.saved) == 1
    _identity, entity, blob, _at = store.saved[0]
    assert entity.entity_id == "c1"
    assert deserialize_float32(blob) == [1.0, 2.0]


def test_skips_unchanged_content_hash() -> None:
    store = _MemoryStore(
        [EmbeddingEntity("c1", 1, "h1", "text")],
        existing={"c1": "h1"},
    )
    litellm = _litellm_returning([[1.0]])
    with patch("propstore.heuristic.embed.require_litellm", return_value=litellm):
        result = embed_entities(store, "m")
    assert result == {"embedded": 0, "skipped": 1, "errors": 0}
    assert store.saved == []


def test_transient_api_error_counts_as_batch_error() -> None:
    store = _MemoryStore([EmbeddingEntity("c1", 1, "h1", "text")])
    litellm = MagicMock()
    litellm.embedding.side_effect = ConnectionError("network down")
    with patch("propstore.heuristic.embed.require_litellm", return_value=litellm):
        result = embed_entities(store, "m")
    assert result == {"embedded": 0, "skipped": 0, "errors": 1}


def test_storage_operational_error_propagates() -> None:
    class _FailingStore(_MemoryStore):
        def existing_content_hashes(
            self, model_identity: EmbeddingModelIdentity
        ) -> Mapping[str, str]:
            raise sqlite3.OperationalError("disk I/O error")

    store = _FailingStore([EmbeddingEntity("c1", 1, "h1", "text")])
    with patch("propstore.heuristic.embed.require_litellm", return_value=MagicMock()):
        with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
            embed_entities(store, "m")


def test_unexpected_provider_error_propagates() -> None:
    store = _MemoryStore([EmbeddingEntity("c1", 1, "h1", "text")])
    litellm = MagicMock()
    litellm.embedding.side_effect = RuntimeError("boom")
    with patch("propstore.heuristic.embed.require_litellm", return_value=litellm):
        with pytest.raises(RuntimeError, match="boom"):
            embed_entities(store, "m")


def test_require_litellm_import_error_is_actionable() -> None:
    from propstore.heuristic import embed

    with patch.object(embed.importlib, "import_module", side_effect=ImportError):
        with pytest.raises(ImportError, match=r"propstore\[embeddings\]"):
            embed.require_litellm()

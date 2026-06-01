"""Embedding helper error propagation tests."""

import sqlite3

import pytest


class TestEmbedEntitiesCallbacks:
    def test_embeds_typed_entities_without_sidecar_schema(self):
        from unittest.mock import MagicMock, patch

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.heuristic.embed import _deserialize_float32, _embed_entities

        prepared = []
        saved = []
        entities = [
            EmbeddingEntity(
                entity_id="c1",
                seq=7,
                content_hash="h1",
                text="claim summary",
            )
        ]
        litellm = MagicMock()
        litellm.embedding.return_value.data = [{"embedding": [1.0, 2.0]}]

        with patch("propstore.heuristic.embed._require_litellm", return_value=litellm):
            result = _embed_entities(
                entities,
                "provider/model",
                existing_content_hashes=lambda _model_identity: {},
                prepare_model=lambda model_identity, dimensions, created_at: (
                    prepared.append((model_identity, dimensions, created_at))
                ),
                save_embedding=lambda model_identity, entity, vector_blob, embedded_at: (
                    saved.append((model_identity, entity, vector_blob, embedded_at))
                ),
            )

        assert result == {"embedded": 1, "skipped": 0, "errors": 0}
        assert prepared
        prepared_identity, dimensions, prepared_at = prepared[0]
        assert prepared_identity.provider == "litellm"
        assert prepared_identity.model_name == "provider/model"
        assert prepared_identity.model_version == ""
        assert prepared_identity.content_digest.startswith("sha256:")
        assert dimensions == 2
        assert len(saved) == 1
        saved_identity, entity, vector_blob, embedded_at = saved[0]
        assert saved_identity == prepared_identity
        assert entity.entity_id == "c1"
        assert _deserialize_float32(vector_blob) == [1.0, 2.0]
        assert embedded_at == prepared_at


class TestEmbedEntitiesOperationalError:
    def test_disk_io_error_propagates_from_status_check(self):
        from unittest.mock import patch, MagicMock

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.heuristic.embed import _embed_entities

        mock_litellm = MagicMock()
        entities = [
            EmbeddingEntity(
                entity_id="c1",
                seq=1,
                content_hash="h1",
                text="summary",
            )
        ]

        with patch(
            "propstore.heuristic.embed._require_litellm", return_value=mock_litellm
        ):
            with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
                _embed_entities(
                    entities,
                    "test-model",
                    existing_content_hashes=lambda _model_identity: (
                        _ for _ in ()
                    ).throw(sqlite3.OperationalError("disk I/O error")),
                    prepare_model=lambda _model_identity, _dimensions, _created_at: (
                        None
                    ),
                    save_embedding=lambda _model_identity, _entity, _blob, _at: None,
                )

    def test_unexpected_embedding_runtime_error_propagates(self):
        """RuntimeError from the embedding provider is not converted to a batch error."""
        from unittest.mock import MagicMock, patch

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.heuristic.embed import _embed_entities

        mock_litellm = MagicMock()
        mock_litellm.embedding.side_effect = RuntimeError("boom")
        entities = [
            EmbeddingEntity(
                entity_id="c1",
                seq=1,
                content_hash="h1",
                text="summary",
            )
        ]

        with patch(
            "propstore.heuristic.embed._require_litellm", return_value=mock_litellm
        ):
            with pytest.raises(RuntimeError, match="boom"):
                _embed_entities(
                    entities,
                    "test-model",
                    existing_content_hashes=lambda _model_identity: {},
                    prepare_model=lambda _model_identity, _dimensions, _created_at: (
                        None
                    ),
                    save_embedding=lambda _model_identity, _entity, _blob, _at: None,
                )

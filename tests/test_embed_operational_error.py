"""Red tests: embed.py broad OperationalError catch swallows non-table errors.

Bug (F1.6-F1.9): embed.py catches ``sqlite3.OperationalError`` in 8 locations,
intending to handle "table doesn't exist" gracefully. But the bare catch
swallows ALL OperationalErrors -- disk full, corruption, permission denied --
and silently returns empty results.

These tests verify that a non-table-missing OperationalError (e.g. "disk I/O
error") propagates to the caller. They should FAIL on current code because
the broad catch swallows them.

Strategy: sqlite3.Connection.execute is read-only on C extension objects,
so we can't patch it directly. Instead we create a thin wrapper class that
delegates to a real connection but raises on targeted queries.
"""

import sqlite3

import pytest


class TestEmbedEntitiesStoreProtocol:
    def test_embeds_entities_supplied_by_store_without_sidecar_schema(self):
        from unittest.mock import MagicMock, patch

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.embed import _deserialize_float32, _embed_entities

        class MemoryStore:
            def __init__(self):
                self.prepared = None
                self.saved = []

            def ensure_storage(self):
                pass

            def load_entities(self, entity_ids=None):
                assert entity_ids == ["c1"]
                return [
                    EmbeddingEntity(
                        entity_id="c1",
                        seq=7,
                        content_hash="h1",
                        text="claim summary",
                    )
                ]

            def existing_content_hashes(self, model_key):
                return {}

            def prepare_model(self, model_key, model_name, dimensions, created_at):
                self.prepared = (model_key, model_name, dimensions, created_at)

            def save_embedding(self, model_key, entity, vector_blob, embedded_at):
                self.saved.append((model_key, entity, vector_blob, embedded_at))

        store = MemoryStore()
        litellm = MagicMock()
        litellm.embedding.return_value.data = [{"embedding": [1.0, 2.0]}]

        with patch("propstore.embed._require_litellm", return_value=litellm):
            result = _embed_entities(store, "provider/model", entity_ids=["c1"])

        assert result == {"embedded": 1, "skipped": 0, "errors": 0}
        assert store.prepared is not None
        assert store.prepared[:3] == ("provider_model", "provider/model", 2)
        assert len(store.saved) == 1
        model_key, entity, vector_blob, embedded_at = store.saved[0]
        assert model_key == "provider_model"
        assert entity.entity_id == "c1"
        assert _deserialize_float32(vector_blob) == [1.0, 2.0]
        assert embedded_at == store.prepared[3]


class _FailingConnection:
    """Wraps a real sqlite3.Connection, raising on targeted SQL patterns.

    Parameters
    ----------
    real_conn : sqlite3.Connection
        The real connection to delegate to.
    fail_pattern : str
        A substring; if it appears in the SQL string, we raise instead.
    error_msg : str
        The OperationalError message to raise.
    """

    def __init__(self, real_conn: sqlite3.Connection, fail_pattern: str, error_msg: str):
        self._real = real_conn
        self._fail_pattern = fail_pattern
        self._error_msg = error_msg

    def execute(self, sql, params=()):
        if self._fail_pattern in sql:
            raise sqlite3.OperationalError(self._error_msg)
        return self._real.execute(sql, params)

    def executescript(self, sql):
        return self._real.executescript(sql)

    def __getattr__(self, name):
        return getattr(self._real, name)


def _make_conn_with_schema():
    """Create an in-memory connection with the tables embed.py expects."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            content_hash TEXT,
            seq INTEGER,
            type TEXT,
            concept_id TEXT,
            target_concept TEXT,
            source_paper TEXT NOT NULL DEFAULT 'test',
            provenance_page INTEGER NOT NULL DEFAULT 1,
            provenance_json TEXT,
            context_id TEXT,
            branch TEXT
        );
        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            lower_bound REAL,
            upper_bound REAL,
            uncertainty REAL,
            uncertainty_type TEXT,
            sample_size INTEGER,
            unit TEXT,
            value_si REAL,
            lower_bound_si REAL,
            upper_bound_si REAL
        );
        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            sympy_generated TEXT,
            sympy_error TEXT,
            name TEXT,
            measure TEXT,
            listener_population TEXT,
            methodology TEXT,
            notes TEXT,
            description TEXT,
            auto_summary TEXT
        );
        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            algorithm_stage TEXT
        );
    """)
    conn.execute(
        """
        INSERT INTO claim_core (
            id, content_hash, seq, type, concept_id, target_concept,
            source_paper, provenance_page, provenance_json, context_id
        ) VALUES ('c1', 'h1', 1, 'observation', NULL, NULL, 'test', 1, NULL, NULL)
        """
    )
    conn.execute(
        "INSERT INTO claim_text_payload VALUES ('c1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'summary')"
    )
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS embedding_model (
            model_key TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS embedding_status (
            model_key TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedded_at TEXT NOT NULL,
            PRIMARY KEY (model_key, claim_id)
        );
        CREATE TABLE IF NOT EXISTS concept_embedding_status (
            model_key TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            embedded_at TEXT NOT NULL,
            PRIMARY KEY (model_key, concept_id)
        );
    """)
    return conn


class TestEmbedEntitiesOperationalError:
    """F1.6: _embed_entities line 198 -- broad OperationalError catch.

    The except block at line 198 catches ALL sqlite3.OperationalError and
    does ``pass``, intending only to handle "table doesn't exist yet". A disk
    I/O error or database corruption error should propagate, not be silenced.
    """

    def test_disk_io_error_propagates_from_status_check(self):
        """A disk I/O OperationalError during status check must propagate.

        Current code swallows it (EXPECTED FAIL).
        """
        from unittest.mock import patch, MagicMock

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.embed import _embed_entities

        class FailingStatusStore:
            def ensure_storage(self):
                pass

            def load_entities(self, entity_ids=None):
                return [
                    EmbeddingEntity(
                        entity_id="c1",
                        seq=1,
                        content_hash="h1",
                        text="summary",
                    )
                ]

            def existing_content_hashes(self, model_key):
                raise sqlite3.OperationalError("disk I/O error")

        mock_litellm = MagicMock()

        with patch("propstore.embed._require_litellm", return_value=mock_litellm):
            # The error should propagate -- not be silently caught
            with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
                _embed_entities(FailingStatusStore(), "test-model")

    def test_unexpected_embedding_runtime_error_propagates(self):
        """RuntimeError from the embedding provider is not converted to a batch error."""
        from unittest.mock import MagicMock, patch

        from propstore.core.embeddings import EmbeddingEntity
        from propstore.embed import _embed_entities

        class MemoryEmbeddingStore:
            def ensure_storage(self):
                pass

            def load_entities(self, entity_ids=None):
                return [
                    EmbeddingEntity(
                        entity_id="c1",
                        seq=1,
                        content_hash="h1",
                        text="summary",
                    )
                ]

            def existing_content_hashes(self, model_key):
                return {}

        mock_litellm = MagicMock()
        mock_litellm.embedding.side_effect = RuntimeError("boom")

        with patch("propstore.embed._require_litellm", return_value=mock_litellm):
            with pytest.raises(RuntimeError, match="boom"):
                _embed_entities(MemoryEmbeddingStore(), "test-model")


class TestGetRegisteredModelsOperationalError:
    """F1.7: get_registered_models line 368 -- broad OperationalError catch.

    The function returns [] on ANY OperationalError, but only "no such table"
    should be treated as "no models yet". A corruption or I/O error must
    propagate.
    """

    def test_disk_io_error_propagates_from_get_models(self):
        """A corruption OperationalError in get_registered_models must propagate.

        Current code returns [] instead (EXPECTED FAIL).
        """
        real_conn = _make_conn_with_schema()
        wrapper = _FailingConnection(
            real_conn, "FROM embedding_model", "database disk image is malformed"
        )

        from propstore.embed import get_registered_models

        with pytest.raises(sqlite3.OperationalError, match="database disk image is malformed"):
            get_registered_models(wrapper)

        real_conn.close()


class TestExtractEmbeddingsOperationalError:
    """F1.9: extract_embeddings line 526 -- broad OperationalError catch.

    extract_embeddings returns None on any OperationalError when reading
    embedding_model. A corruption error should propagate.
    """

    def test_corruption_error_propagates_from_extract(self):
        """A corruption OperationalError in extract_embeddings must propagate.

        Current code returns None instead (EXPECTED FAIL).
        """
        real_conn = _make_conn_with_schema()
        wrapper = _FailingConnection(
            real_conn, "FROM embedding_model", "database disk image is malformed"
        )

        from propstore.embed import extract_embeddings

        with pytest.raises(sqlite3.OperationalError, match="database disk image is malformed"):
            extract_embeddings(wrapper)

        real_conn.close()

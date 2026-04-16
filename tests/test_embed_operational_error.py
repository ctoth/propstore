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

        real_conn = _make_conn_with_schema()

        # Wrap: blow up when _embed_entities queries embedding_status
        wrapper = _FailingConnection(real_conn, "FROM embedding_status", "disk I/O error")

        from propstore.embed import _embed_entities, _EmbedConfig

        config = _EmbedConfig(
            entity_table="""
                (
                    SELECT
                        core.id,
                        core.seq,
                        core.content_hash,
                        txt.auto_summary,
                        txt.statement,
                        txt.expression,
                        txt.name
                    FROM claim_core AS core
                    LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
                )
            """,
            select_columns="id, seq, content_hash, auto_summary, statement, expression, name",
            status_table="embedding_status",
            status_id_column="claim_id",
            vec_prefix="claim_vec",
            text_builder=lambda e, _: str(e["id"]),
            pre_batch_hook=None,
        )

        mock_litellm = MagicMock()

        with patch("propstore.embed._require_litellm", return_value=mock_litellm):
            # The error should propagate -- not be silently caught
            with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
                _embed_entities(wrapper, "test-model", config)

        real_conn.close()


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

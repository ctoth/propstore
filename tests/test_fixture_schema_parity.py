from __future__ import annotations

import sqlite3

import tests.conftest as project_conftest

from quire.derived_runtime import write_derived_store_schema_metadata

from propstore.sidecar import schema
from propstore.families.micropublications.declaration import create_micropublication_tables
from propstore.families.embeddings.declaration import ensure_embedding_tables
from propstore.families.rules.declaration import create_grounded_fact_table


def _table_info(conn: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA table_info({table})"))


def _index_list(conn: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA index_list({table})"))


def _foreign_key_list(conn: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA foreign_key_list({table})"))


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        """
    )
    return {str(row[0]) for row in rows}


def test_world_query_fixture_schema_is_built_by_production_helper() -> None:
    assert not hasattr(project_conftest, "create_world_model_schema")
    assert hasattr(schema, "build_minimal_world_model_schema")


def test_minimal_world_model_schema_matches_production_builders() -> None:
    fixture_conn = sqlite3.connect(":memory:")
    production_conn = sqlite3.connect(":memory:")

    schema.build_minimal_world_model_schema(fixture_conn)
    write_derived_store_schema_metadata(
        production_conn,
        schema_version=schema.SCHEMA_VERSION,
        key=schema.SIDECAR_META_KEY,
    )
    schema.create_tables(production_conn)
    schema.create_context_tables(production_conn)
    schema.create_claim_tables(production_conn)
    create_micropublication_tables(production_conn)
    create_grounded_fact_table(production_conn)
    ensure_embedding_tables(production_conn)

    assert _table_names(fixture_conn) == _table_names(production_conn)
    for table in sorted(_table_names(production_conn)):
        assert _table_info(fixture_conn, table) == _table_info(production_conn, table)
        assert _index_list(fixture_conn, table) == _index_list(production_conn, table)
        assert _foreign_key_list(fixture_conn, table) == _foreign_key_list(production_conn, table)

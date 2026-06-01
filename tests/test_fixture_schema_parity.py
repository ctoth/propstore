from __future__ import annotations

import sqlite3
from sqlite3 import Connection
from pathlib import Path

import tests.conftest as project_conftest

from sqlalchemy import create_engine

from propstore.families.registry import world_schema
from tests.sidecar_schema_helpers import build_world_projection_schema


def _table_info(conn: Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA table_info({table})"))


def _index_list(conn: Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA index_list({table})"))


def _foreign_key_list(conn: Connection, table: str) -> list[tuple[object, ...]]:
    return list(conn.execute(f"PRAGMA foreign_key_list({table})"))


def _table_names(conn: Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        """
    )
    return {str(row[0]) for row in rows}


def test_world_query_fixture_schema_is_built_from_world_schema() -> None:
    assert not hasattr(project_conftest, "create_world_model_schema")
    assert not (
        Path(__file__).parents[1] / "propstore" / "sidecar" / "schema.py"
    ).exists()

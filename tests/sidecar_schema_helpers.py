from __future__ import annotations

import json
import sqlite3
from sqlite3 import Connection

from sqlalchemy import create_engine, insert, text

from propstore.families.meta.declaration import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
)
from propstore.families.registry import world_schema
from propstore.families.sources.declaration import SourceOrigin, SourceTrust


def build_world_projection_schema(conn: Connection) -> None:
    schema = world_schema()
    engine = create_engine("sqlite://", creator=lambda: conn)
    schema.metadata.create_all(engine)
    with engine.begin() as sql_conn:
        sql_conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS quire_schema_catalog (
                    key TEXT PRIMARY KEY,
                    schema_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
        )
        sql_conn.execute(
            text(
                """
                INSERT INTO quire_schema_catalog (key, schema_hash, payload_json)
                VALUES (:key, :schema_hash, :payload_json)
                ON CONFLICT(key) DO UPDATE SET
                    schema_hash = excluded.schema_hash,
                    payload_json = excluded.payload_json
                """
            ),
            {
                "key": "default",
                "schema_hash": schema.catalog_hash,
                "payload_json": json.dumps(
                    schema.catalog.payload(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            },
        )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, schema_version) VALUES (?, ?)",
        (PROPSTORE_WORLD_META_KEY, PROPSTORE_WORLD_SCHEMA_VERSION),
    )
    conn.commit()


def insert_minimal_source(
    conn: Connection,
    *,
    slug: str = "test-source",
    source_id: str | None = None,
    kind: str = "academic_paper",
    origin_type: str = "manual",
    origin_value: str = "fixture",
    trust_status: str = "stated",
) -> None:
    schema = world_schema()
    engine = create_engine("sqlite://", creator=lambda: conn)
    with engine.begin() as sql_conn:
        sql_conn.execute(
            insert(schema.table("source")).prefix_with("OR IGNORE"),
            {
                "slug": slug,
                "source_id": source_id or slug,
                "kind": kind,
                "origin": SourceOrigin(type=origin_type, value=origin_value),
                "trust": SourceTrust(status=trust_status),
            },
        )

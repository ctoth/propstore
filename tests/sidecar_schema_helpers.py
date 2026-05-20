from __future__ import annotations

import json
import sqlite3

from sqlalchemy import create_engine, text

from propstore.families.world_charters import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
    world_sqlalchemy_schema,
)


def build_world_projection_schema(conn: sqlite3.Connection) -> None:
    schema = world_sqlalchemy_schema()
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

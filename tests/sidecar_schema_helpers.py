from __future__ import annotations

import sqlite3

from quire.derived_runtime import write_derived_store_schema_metadata

from propstore.families.projection_catalog import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_PROJECTION_SCHEMA,
    PROPSTORE_WORLD_SCHEMA_VERSION,
)


def build_world_projection_schema(conn: sqlite3.Connection) -> None:
    write_derived_store_schema_metadata(
        conn,
        schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
        key=PROPSTORE_WORLD_META_KEY,
    )
    PROPSTORE_WORLD_PROJECTION_SCHEMA.create_all(conn)
    conn.commit()

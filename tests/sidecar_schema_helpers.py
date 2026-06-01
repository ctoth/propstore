from __future__ import annotations

import json
from sqlite3 import Connection

from sqlalchemy import create_engine, insert, text

from propstore.families.meta.declaration import (
    PROPSTORE_WORLD_META_KEY,
    PROPSTORE_WORLD_SCHEMA_VERSION,
)
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.sources.declaration import (
    SourceOriginDocument,
    SourceTrustDocument,
)
from propstore.families.registry import world_schema
from propstore.provenance import ProvenanceStatus


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
                "kind": SourceKind(kind),
                "origin": SourceOriginDocument(
                    type=SourceOriginType(origin_type),
                    value=origin_value,
                ),
                "trust": SourceTrustDocument(status=ProvenanceStatus(trust_status)),
            },
        )

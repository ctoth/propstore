"""Source SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from propstore.sidecar.projection import ProjectionColumn, ProjectionIndex, ProjectionTable


SOURCE_PROJECTION = ProjectionTable(
    name="source",
    columns=(
        ProjectionColumn("slug", "TEXT", primary_key=True),
        ProjectionColumn("source_id", "TEXT", nullable=False),
        ProjectionColumn("kind", "TEXT", nullable=False),
        ProjectionColumn("origin_type", "TEXT"),
        ProjectionColumn("origin_value", "TEXT"),
        ProjectionColumn("origin_retrieved", "TEXT"),
        ProjectionColumn("origin_content_ref", "TEXT"),
        ProjectionColumn("prior_base_rate", "TEXT"),
        ProjectionColumn("quality_json", "TEXT"),
        ProjectionColumn("derived_from_json", "TEXT"),
        ProjectionColumn("artifact_code", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_source_source_id", ("source_id",)),),
)


@dataclass(frozen=True)
class SourceProjectionRow:
    slug: str
    source_id: str
    kind: str
    origin_type: str | None
    origin_value: str | None
    origin_retrieved: str | None
    origin_content_ref: str | None
    prior_base_rate: str | None
    quality_json: str | None
    derived_from_json: str | None
    artifact_code: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "slug": self.slug,
            "source_id": self.source_id,
            "kind": self.kind,
            "origin_type": self.origin_type,
            "origin_value": self.origin_value,
            "origin_retrieved": self.origin_retrieved,
            "origin_content_ref": self.origin_content_ref,
            "prior_base_rate": self.prior_base_rate,
            "quality_json": self.quality_json,
            "derived_from_json": self.derived_from_json,
            "artifact_code": self.artifact_code,
        }


def populate_sources(conn: sqlite3.Connection, rows: Sequence[SourceProjectionRow]) -> None:
    insert_sql = SOURCE_PROJECTION.insert_sql()
    for row in rows:
        conn.execute(insert_sql, row.as_insert_mapping())

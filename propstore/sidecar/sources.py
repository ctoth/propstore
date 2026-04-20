"""Source SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3

from propstore.sidecar.stages import SourceSidecarRows


def populate_sources(
    conn: sqlite3.Connection,
    rows: SourceSidecarRows,
) -> None:
    for row in rows.source_rows:
        conn.execute(
            "INSERT INTO source (slug, source_id, kind, origin_type, "
            "origin_value, origin_retrieved, origin_content_ref, "
            "prior_base_rate, quality_json, derived_from_json, artifact_code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row.values,
        )

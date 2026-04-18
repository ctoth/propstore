"""Source compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable

from propstore.artifacts.documents.sources import SourceDocument


def populate_sources(conn: sqlite3.Connection, sources: Iterable[tuple[str, SourceDocument]]) -> None:
    """Populate the compiled source table from canonical source YAML."""
    for slug, source_doc in sources:
        origin = source_doc.origin
        trust = source_doc.trust
        conn.execute(
            "INSERT INTO source (slug, source_id, kind, origin_type, origin_value, origin_retrieved, "
            "origin_content_ref, prior_base_rate, quality_json, derived_from_json, artifact_code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                slug,
                str(source_doc.id or slug),
                source_doc.kind.value,
                origin.type.value,
                origin.value,
                origin.retrieved,
                origin.content_ref,
                trust.prior_base_rate,
                None if trust.quality is None else json.dumps(trust.quality.to_payload()),
                None if not trust.derived_from else json.dumps(list(trust.derived_from)),
                source_doc.artifact_code,
            ),
        )

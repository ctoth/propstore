"""Source compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3

from propstore.document_schema import decode_document_path
from propstore.knowledge_path import KnowledgePath
from propstore.source_documents import SourceDocument


def populate_sources(conn: sqlite3.Connection, knowledge_root: KnowledgePath) -> None:
    """Populate the compiled source table from canonical source YAML."""
    sources_root = knowledge_root / "sources"
    if not sources_root.exists():
        return
    for entry in sources_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        source_doc = decode_document_path(entry, SourceDocument)
        origin = source_doc.origin
        trust = source_doc.trust
        conn.execute(
            "INSERT INTO source (slug, source_id, kind, origin_type, origin_value, origin_retrieved, "
            "origin_content_ref, prior_base_rate, quality_json, derived_from_json, artifact_code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.stem,
                str(source_doc.id or entry.stem),
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

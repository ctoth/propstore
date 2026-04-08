"""Source compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3

import yaml

from propstore.knowledge_path import KnowledgePath


def populate_sources(conn: sqlite3.Connection, knowledge_root: KnowledgePath) -> None:
    """Populate the compiled source table from canonical source YAML."""
    sources_root = knowledge_root / "sources"
    if not sources_root.exists():
        return
    for entry in sources_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        source_doc = yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
        if not isinstance(source_doc, dict):
            continue
        origin = source_doc.get("origin") if isinstance(source_doc.get("origin"), dict) else {}
        trust = source_doc.get("trust") if isinstance(source_doc.get("trust"), dict) else {}
        conn.execute(
            "INSERT INTO source (slug, source_id, kind, origin_type, origin_value, origin_retrieved, "
            "origin_content_ref, prior_base_rate, quality_json, derived_from_json, artifact_code) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.stem,
                str(source_doc.get("id") or entry.stem),
                str(source_doc.get("kind") or "source"),
                origin.get("type"),
                origin.get("value"),
                origin.get("retrieved"),
                origin.get("content_ref"),
                trust.get("prior_base_rate"),
                json.dumps(trust.get("quality")) if trust.get("quality") is not None else None,
                json.dumps(trust.get("derived_from")) if trust.get("derived_from") is not None else None,
                source_doc.get("artifact_code"),
            ),
        )

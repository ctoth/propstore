"""Micropublication SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3

from propstore.sidecar.stages import MicropublicationSidecarRows


def populate_micropublications(
    conn: sqlite3.Connection,
    rows: MicropublicationSidecarRows,
) -> None:
    """Populate micropublication tables from compiled sidecar rows.

    ``micropublication.id`` is derived from the full canonical payload by WS-CM.
    Identical authored payloads produce the same id; changing
    authored content produces a new id. First-writer-wins dedupe on the
    id is therefore safe, and link dedupe uses
    ``(micropublication_id, claim_id)`` as the composite key.
    """

    seen_micropub_ids: set[str] = set()
    for row in rows.micropublication_rows:
        micropub_id = row.values[0] if row.values else None
        if isinstance(micropub_id, str) and micropub_id in seen_micropub_ids:
            continue
        conn.execute(
            """
            INSERT INTO micropublication (
                id, context_id, assumptions_json, evidence_json,
                stance, provenance_json, source_slug
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )
        if isinstance(micropub_id, str):
            seen_micropub_ids.add(micropub_id)

    seen_link_keys: set[tuple[str, str]] = set()
    for row in rows.claim_rows:
        if len(row.values) >= 2:
            micropub_id = row.values[0]
            claim_id = row.values[1]
            if isinstance(micropub_id, str) and isinstance(claim_id, str):
                key = (micropub_id, claim_id)
                if key in seen_link_keys:
                    continue
                seen_link_keys.add(key)
        conn.execute(
            """
            INSERT INTO micropublication_claim (micropublication_id, claim_id, seq)
            VALUES (?, ?, ?)
            """,
            row.values,
        )

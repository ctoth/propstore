"""Micropublication SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3

from propstore.sidecar.stages import MicropublicationSidecarRows


def populate_micropublications(
    conn: sqlite3.Connection,
    rows: MicropublicationSidecarRows,
) -> None:
    for row in rows.micropublication_rows:
        conn.execute(
            """
            INSERT INTO micropublication (
                id, context_id, assumptions_json, evidence_json,
                stance, provenance_json, source_slug
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )
    for row in rows.claim_rows:
        conn.execute(
            """
            INSERT INTO micropublication_claim (micropublication_id, claim_id, seq)
            VALUES (?, ?, ?)
            """,
            row.values,
        )

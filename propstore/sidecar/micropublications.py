"""Micropublication SQL insertion helpers for the sidecar."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass

from quire.projections import (
    ProjectionColumn,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionTable,
)
from propstore.sidecar.stages import MicropublicationSidecarRows


MICROPUBLICATION_PROJECTION = ProjectionTable(
    name="micropublication",
    columns=(
        ProjectionColumn("id", "TEXT", nullable=False, primary_key=True),
        ProjectionColumn("context_id", "TEXT", nullable=False),
        ProjectionColumn(
            "assumptions_json",
            "TEXT",
            nullable=False,
            default_sql="'[]'",
        ),
        ProjectionColumn(
            "evidence_json",
            "TEXT",
            nullable=False,
            default_sql="'[]'",
        ),
        ProjectionColumn("stance", "TEXT"),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("source_slug", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(ProjectionIndex("idx_micropub_context", ("context_id",)),),
    if_not_exists=True,
)


MICROPUBLICATION_CLAIM_PROJECTION = ProjectionTable(
    name="micropublication_claim",
    columns=(
        ProjectionColumn("micropublication_id", "TEXT", nullable=False),
        ProjectionColumn("claim_id", "TEXT", nullable=False),
        ProjectionColumn("seq", "INTEGER", nullable=False),
    ),
    primary_key=("micropublication_id", "claim_id"),
    foreign_keys=(
        ProjectionForeignKey(("micropublication_id",), "micropublication", ("id",)),
        ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),
    ),
    indexes=(ProjectionIndex("idx_micropub_claim", ("claim_id",)),),
    if_not_exists=True,
)


@dataclass(frozen=True)
class MicropublicationProjectionRow:
    id: str
    context_id: str
    assumptions_json: str
    evidence_json: str
    stance: str | None
    provenance_json: str | None
    source_slug: str | None

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "context_id": self.context_id,
            "assumptions_json": self.assumptions_json,
            "evidence_json": self.evidence_json,
            "stance": self.stance,
            "provenance_json": self.provenance_json,
            "source_slug": self.source_slug,
        }


@dataclass(frozen=True)
class MicropublicationClaimProjectionRow:
    micropublication_id: str
    claim_id: str
    seq: int

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "micropublication_id": self.micropublication_id,
            "claim_id": self.claim_id,
            "seq": self.seq,
        }


def create_micropublication_tables(conn: sqlite3.Connection) -> None:
    for projection in (
        MICROPUBLICATION_PROJECTION,
        MICROPUBLICATION_CLAIM_PROJECTION,
    ):
        for statement in projection.ddl_statements():
            conn.execute(statement)


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
    micropublication_insert_sql = MICROPUBLICATION_PROJECTION.insert_sql()
    for row in rows.micropublication_rows:
        if row.id in seen_micropub_ids:
            continue
        conn.execute(micropublication_insert_sql, row.as_insert_mapping())
        seen_micropub_ids.add(row.id)

    seen_link_keys: set[tuple[str, str]] = set()
    micropublication_claim_insert_sql = MICROPUBLICATION_CLAIM_PROJECTION.insert_sql()
    for row in rows.claim_rows:
        key = (row.micropublication_id, row.claim_id)
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        conn.execute(
            micropublication_claim_insert_sql,
            row.as_insert_mapping(),
        )

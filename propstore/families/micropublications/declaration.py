"""Micropublication derived-store declaration and query helpers."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass

from quire.projections import (
    ARTIFACT_ID_FIELD,
    PROVENANCE_JSON_FIELD,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionTable,
    SEQUENCE_FIELD,
    family_reference_field,
    text_field,
)
from quire.references import FamilyReferenceIndex

from propstore.core.micropublications import ActiveMicropublication
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.documents.micropubs import MicropublicationDocument


MICROPUBLICATION_PROJECTION = ProjectionTable(
    name="micropublication",
    columns=(
        ARTIFACT_ID_FIELD.column(nullable=False, primary_key=True),
        family_reference_field("context", nullable=False).column(),
        text_field("assumptions_json", nullable=False).column(default_sql="'[]'"),
        text_field("evidence_json", nullable=False).column(default_sql="'[]'"),
        text_field("stance").column(),
        PROVENANCE_JSON_FIELD.column(),
        text_field("source_slug").column(),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(ProjectionIndex("idx_micropub_context", ("context_id",)),),
    if_not_exists=True,
)


MICROPUBLICATION_CLAIM_PROJECTION = ProjectionTable(
    name="micropublication_claim",
    columns=(
        family_reference_field("micropublication", nullable=False).column(),
        family_reference_field("claim", nullable=False).column(),
        SEQUENCE_FIELD.column(),
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


@dataclass(frozen=True)
class MicropublicationClaimProjectionRow:
    micropublication_id: str
    claim_id: str
    seq: int


@dataclass(frozen=True)
class MicropublicationSidecarRows:
    micropublication_rows: tuple[MicropublicationProjectionRow, ...]
    claim_rows: tuple[MicropublicationClaimProjectionRow, ...]


def compile_micropublication_sidecar_rows(
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> MicropublicationSidecarRows:
    rows, diagnostics = compile_micropublication_sidecar_rows_with_diagnostics(
        micropub_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def compile_micropublication_sidecar_rows_with_diagnostics(
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[MicropublicationSidecarRows, tuple[QuarantineDiagnostic, ...]]:
    valid_claim_ids = set(claim_index.ids())
    micropublication_rows: list[MicropublicationProjectionRow] = []
    claim_rows: list[MicropublicationClaimProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, micropub in sorted(micropub_entries, key=lambda item: item[0]):
        resolved_claims: list[str] = []
        missing_claim_ref: str | None = None
        for claim_id in micropub.claims:
            resolved_claim = claim_index.resolve_id(claim_id)
            if (
                not isinstance(resolved_claim, str)
                or resolved_claim not in valid_claim_ids
            ):
                if isinstance(resolved_claim, str) and resolved_claim:
                    missing_claim_ref = resolved_claim
                elif isinstance(claim_id, str) and claim_id:
                    missing_claim_ref = claim_id
                else:
                    missing_claim_ref = micropub.artifact_id
                break
            resolved_claims.append(resolved_claim)
        if missing_claim_ref is not None:
            message = (
                f"micropublication artifact {micropub.artifact_id} references "
                f"nonexistent claim '{missing_claim_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_claim_ref,
                    kind="micropublication",
                    diagnostic_kind="micropublication_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        micropublication_rows.append(
            MicropublicationProjectionRow(
                id=micropub.artifact_id,
                context_id=str(micropub.context.id),
                assumptions_json=json.dumps(
                    list(micropub.assumptions),
                    sort_keys=True,
                ),
                evidence_json=json.dumps(
                    [item.to_payload() for item in micropub.evidence],
                    sort_keys=True,
                ),
                stance=None if micropub.stance is None else micropub.stance.value,
                provenance_json=(
                    None
                    if micropub.provenance is None
                    else json.dumps(
                        micropub.provenance.to_payload(),
                        sort_keys=True,
                    )
                ),
                source_slug=micropub.source,
            )
        )
        for seq, claim_id in enumerate(resolved_claims, start=1):
            claim_rows.append(
                MicropublicationClaimProjectionRow(
                    micropublication_id=micropub.artifact_id,
                    claim_id=claim_id,
                    seq=seq,
                )
            )

    return (
        MicropublicationSidecarRows(
            micropublication_rows=tuple(micropublication_rows),
            claim_rows=tuple(claim_rows),
        ),
        tuple(diagnostics),
    )


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
    for row in rows.micropublication_rows:
        if row.id in seen_micropub_ids:
            continue
        MICROPUBLICATION_PROJECTION.insert_row(conn, row)
        seen_micropub_ids.add(row.id)

    seen_link_keys: set[tuple[str, str]] = set()
    for row in rows.claim_rows:
        key = (row.micropublication_id, row.claim_id)
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        MICROPUBLICATION_CLAIM_PROJECTION.insert_row(conn, row)


def select_all_micropublications(
    conn: sqlite3.Connection,
) -> list[ActiveMicropublication]:
    rows = conn.execute(
        """
        SELECT
            mp.id AS artifact_id,
            mp.context_id,
            mp.assumptions_json,
            mp.stance,
            mp.source_slug,
            (
                SELECT json_group_array(mc.claim_id)
                FROM micropublication_claim mc
                WHERE mc.micropublication_id = mp.id
                ORDER BY mc.seq
            ) AS claim_ids
        FROM micropublication mp
        ORDER BY mp.id
        """
    ).fetchall()
    return [
        ActiveMicropublication.from_mapping(
            {
                "artifact_id": row["artifact_id"],
                "context_id": row["context_id"],
                "claim_ids": row["claim_ids"],
                "assumptions": row["assumptions_json"],
                "stance": row["stance"],
                "source": row["source_slug"],
            }
        )
        for row in rows
    ]

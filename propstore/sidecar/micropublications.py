"""Populate sidecar micropublication tables from canonical artifacts."""

from __future__ import annotations

import json
import sqlite3

from propstore.artifacts.documents.micropubs import MicropublicationsFileDocument
from quire.documents import decode_document_path
from quire.tree_path import TreePath as KnowledgePath
from propstore.sidecar.claim_utils import claim_reference_map_from_conn, resolve_claim_reference


def populate_micropublications(conn: sqlite3.Connection, micropubs_root: KnowledgePath) -> int:
    if not micropubs_root.exists():
        return 0

    claim_reference_map = claim_reference_map_from_conn(conn)
    valid_claim_ids = set(claim_reference_map.values())
    count = 0

    for entry in sorted(micropubs_root.iterdir(), key=lambda item: item.name):
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        document = decode_document_path(entry, MicropublicationsFileDocument)
        for micropub in document.micropubs:
            resolved_claims = [
                resolve_claim_reference(claim_id, claim_reference_map)
                for claim_id in micropub.claims
            ]
            if any(claim_id not in valid_claim_ids for claim_id in resolved_claims):
                raise sqlite3.IntegrityError(
                    f"micropublication {micropub.artifact_id} references nonexistent claim"
                )

            conn.execute(
                """
                INSERT INTO micropublication (
                    id, context_id, assumptions_json, evidence_json,
                    stance, provenance_json, source_slug
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    micropub.artifact_id,
                    str(micropub.context.id),
                    json.dumps(list(micropub.assumptions), sort_keys=True),
                    json.dumps([item.to_payload() for item in micropub.evidence], sort_keys=True),
                    None if micropub.stance is None else micropub.stance.value,
                    (
                        None
                        if micropub.provenance is None
                        else json.dumps(micropub.provenance.to_payload(), sort_keys=True)
                    ),
                    micropub.source,
                ),
            )
            for seq, claim_id in enumerate(resolved_claims, start=1):
                assert claim_id is not None
                conn.execute(
                    """
                    INSERT INTO micropublication_claim (micropublication_id, claim_id, seq)
                    VALUES (?, ?, ?)
                    """,
                    (micropub.artifact_id, claim_id, seq),
                )
            count += 1
    return count

"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from typing import TYPE_CHECKING

from propstore.claims import (
    LoadedClaimsFile,
    claim_file_claims,
    claim_file_source_paper,
    claim_file_stage,
)
from propstore.artifacts.schema import decode_document_path
from propstore.knowledge_path import KnowledgePath
from propstore.sidecar.claim_utils import (
    claim_reference_map_from_conn,
    coerce_stance_resolution,
    collect_claim_reference_map,
    extract_deferred_stance_rows,
    insert_claim_row,
    insert_claim_stance_row,
    prepare_claim_insert_row,
    resolution_opinion_columns,
    resolve_claim_reference,
)
from propstore.artifacts.documents.sources import SourceJustificationsDocument
from propstore.artifacts.documents.stances import StanceFileDocument
from propstore.stances import VALID_STANCE_TYPES

if TYPE_CHECKING:
    from propstore.compiler.ir import ClaimCompilationBundle
    from propstore.sidecar.build import RawIdQuarantineRecord


def populate_stances_from_files(
    conn: sqlite3.Connection,
    stances_root: KnowledgePath,
) -> int:
    """Read stance YAML files and insert them into normalized relation storage."""
    if not stances_root.exists():
        return 0
    stance_entries = [
        (entry.stem, decode_document_path(entry, StanceFileDocument))
        for entry in stances_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    if not stance_entries:
        return 0

    claim_reference_map = claim_reference_map_from_conn(conn)
    valid_claims = set(claim_reference_map.values())
    count = 0

    for filename, data in stance_entries:
        source_claim = resolve_claim_reference(
            data.source_claim,
            claim_reference_map,
        ) or ""
        if source_claim not in valid_claims:
            raise sqlite3.IntegrityError(
                f"stance file {filename} references nonexistent source claim '{source_claim}'"
            )

        for index, stance in enumerate(data.stances, start=1):
            stance_payload = stance.to_payload()
            target = resolve_claim_reference(
                stance.target or "",
                claim_reference_map,
            ) or ""
            stance_type = stance.type or ""
            if target not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"stance file {filename} references nonexistent target claim '{target}'"
                )
            if stance_type not in VALID_STANCE_TYPES:
                raise ValueError(
                    f"stance file {filename} uses unrecognized stance type '{stance_type}'"
                )

            resolution = coerce_stance_resolution(
                stance_payload.get("resolution"),
                f"stance file {filename} stance #{index}",
            )
            opinion_columns = resolution_opinion_columns(resolution)
            conditions_differ = stance.conditions_differ

            insert_claim_stance_row(
                conn,
                (
                    source_claim,
                    target,
                    stance_type,
                    stance.target_justification_id,
                    stance.strength,
                    conditions_differ,
                    stance.note,
                    resolution.get("method"),
                    resolution.get("model"),
                    resolution.get("embedding_model"),
                    resolution.get("embedding_distance"),
                    resolution.get("pass_number"),
                    resolution.get("confidence"),
                    opinion_columns[0],
                    opinion_columns[1],
                    opinion_columns[2],
                    opinion_columns[3],
                ),
            )
            count += 1
    return count


def populate_authored_justifications_from_files(
    conn: sqlite3.Connection,
    justifications_root: KnowledgePath,
) -> int:
    """Read authored justification YAML files and insert them into the sidecar."""
    if not justifications_root.exists():
        return 0

    justification_entries = [
        (entry.stem, decode_document_path(entry, SourceJustificationsDocument))
        for entry in justifications_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    if not justification_entries:
        return 0

    claim_reference_map = claim_reference_map_from_conn(conn)
    valid_claims = set(claim_reference_map.values())
    count = 0

    for filename, data in justification_entries:
        for index, justification in enumerate(data.justifications, start=1):
            justification_payload = justification.to_payload()
            justification_id = justification.id
            conclusion = resolve_claim_reference(
                justification.conclusion,
                claim_reference_map,
            )
            if not isinstance(justification_id, str) or not justification_id:
                raise ValueError(f"justification file {filename} entry #{index} missing id")
            if not isinstance(conclusion, str) or conclusion not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"justification file {filename} entry #{index} references nonexistent conclusion '{conclusion}'"
                )
            resolved_premises = [
                resolve_claim_reference(premise, claim_reference_map)
                for premise in justification.premises
            ]
            if any(
                not isinstance(premise, str) or premise not in valid_claims
                for premise in resolved_premises
            ):
                raise sqlite3.IntegrityError(
                    f"justification file {filename} entry #{index} references nonexistent premise"
                )

            provenance = justification_payload.get("provenance")
            attack_target = justification_payload.get("attack_target")
            provenance_payload: dict[str, object] = {}
            if isinstance(provenance, dict):
                provenance_payload.update(provenance)
            if isinstance(attack_target, dict):
                provenance_payload["attack_target"] = attack_target

            conn.execute(
                "INSERT OR IGNORE INTO justification "
                "(id, justification_kind, conclusion_claim_id, premise_claim_ids, "
                "source_relation_type, source_claim_id, provenance_json, rule_strength) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    justification_id,
                    str(justification.rule_kind or "reported_claim"),
                    conclusion,
                    json.dumps(resolved_premises),
                    None,
                    None,
                    json.dumps(provenance_payload) if provenance_payload else None,
                    str(justification.rule_strength or "defeasible"),
                ),
            )
            count += 1
    return count


def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    records: Sequence[RawIdQuarantineRecord],
) -> None:
    """Write stub claim_core + build_diagnostics rows for raw-id-broken claims.

    Per ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    axis-1 finding 3.1: the former all-or-nothing abort on raw-id inputs
    becomes a per-claim quarantine. Each record yields:

    - One ``claim_core`` row with ``id=<synthetic>``,
      ``build_status='blocked'``, and minimal required fields. The
      synthetic id scheme and basis are recorded in ``detail_json`` on
      the paired diagnostic row for traceability (CLAUDE.md
      honest-ignorance discipline — do not hide that the id is synthetic).
    - One ``build_diagnostics`` row with
      ``diagnostic_kind='raw_id_input'``, ``blocking=1``,
      ``severity='error'``, ``claim_id=<synthetic>``.

    Render-policy filters hide ``build_status='blocked'`` rows by default
    (phase 4).
    """

    for record in records:
        # Stub claim_core row — minimal required columns; FK nullable fields
        # left NULL. The existing ``insert_claim_row`` helper expects a full
        # payload dict and pushes to three payload tables; for a pure
        # quarantine row we only need the core row. Use a direct INSERT.
        conn.execute(
            """
            INSERT INTO claim_core (
                id, primary_logical_id, logical_ids_json, version_id,
                content_hash, seq, type, concept_id, target_concept,
                source_slug, source_paper, provenance_page, provenance_json,
                context_id, premise_kind, branch, build_status, stage,
                promotion_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.synthetic_id,
                "",
                "[]",
                "",
                "",
                record.seq,
                "quarantine",
                None,
                None,
                record.source_paper,
                record.source_paper,
                0,
                None,
                None,
                "ordinary",
                None,
                "blocked",
                None,
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.synthetic_id,
                "claim",
                record.raw_id,
                "raw_id_input",
                "error",
                1,
                record.message,
                record.filename,
                record.detail_json,
            ),
        )


def populate_claims(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedClaimsFile],
    concept_registry: dict | None = None,
    *,
    form_registry: dict | None = None,
    semantic_bundle: ClaimCompilationBundle | None = None,
) -> None:
    """Populate normalized claim storage from authored claim files.

    Schema-v3 behavior (``reviews/2026-04-16-code-review/workstreams/
    ws-z-render-gates.md`` finding 3.2): the file-level ``stage`` marker
    (e.g. ``'draft'``) is threaded from the claim-file document onto each
    ``claim_core`` row. Drafts populate normally; render-policy filtering
    (phase 4) decides visibility.
    """

    claim_seq = 0
    deferred_stances: list[tuple] = []
    reference_source = (
        list(semantic_bundle.normalized_claim_files)
        if semantic_bundle is not None
        else list(claim_files)
    )
    claim_reference_map = collect_claim_reference_map(reference_source)
    # Filename → file-level stage marker. Used to annotate ``claim_core.stage``
    # on every row for the file (draft, final, or NULL). Consulted both on
    # the semantic-bundle path (via ``SemanticClaim.filename``) and the
    # raw-claim-file path (via ``claim_file.filename``).
    file_stage_by_filename: dict[str, str | None] = {
        claim_file.filename: claim_file_stage(claim_file)
        for claim_file in reference_source
    }

    if semantic_bundle is not None:
        for semantic_file in semantic_bundle.semantic_files:
            file_stage = file_stage_by_filename.get(
                semantic_file.normalized_entry.filename
            )
            for semantic_claim in semantic_file.claims:
                claim_seq += 1
                row = prepare_claim_insert_row(
                    semantic_claim,
                    semantic_claim.source_paper,
                    claim_seq=claim_seq,
                    concept_registry=concept_registry,
                    form_registry=form_registry,
                )
                if file_stage is not None:
                    row["stage"] = file_stage
                insert_claim_row(conn, row)
                deferred_stances.extend(
                    extract_deferred_stance_rows(
                        semantic_claim,
                        claim_reference_map,
                        source_paper=semantic_claim.source_paper,
                    )
                )
    else:
        for claim_file in claim_files:
            source_paper = claim_file_source_paper(claim_file) or claim_file.filename
            file_stage = file_stage_by_filename.get(claim_file.filename)
            for claim in claim_file_claims(claim_file):
                authored_claim = claim.to_payload()
                claim_seq += 1
                row = prepare_claim_insert_row(
                    authored_claim,
                    source_paper,
                    claim_seq=claim_seq,
                    concept_registry=concept_registry,
                    form_registry=form_registry,
                )
                if file_stage is not None:
                    row["stage"] = file_stage
                insert_claim_row(conn, row)
                deferred_stances.extend(
                    extract_deferred_stance_rows(
                        authored_claim,
                        claim_reference_map,
                        source_paper=source_paper,
                    )
                )

    for stance_row in deferred_stances:
        insert_claim_stance_row(conn, stance_row)


def populate_conflicts(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedClaimsFile],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> None:
    from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
    from propstore.conflict_detector.collectors import conflict_claims_from_claim_files

    conflict_claims = conflict_claims_from_claim_files(claim_files)
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    transitive_records = detect_transitive_conflicts(
        conflict_claims,
        concept_registry,
        lifting_system=lifting_system,
    )
    records.extend(transitive_records)
    for record in records:
        conn.execute(
            "INSERT INTO conflict_witness (concept_id, claim_a_id, claim_b_id, "
            "warning_class, conditions_a, conditions_b, value_a, value_b, "
            "derivation_chain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.concept_id,
                record.claim_a_id,
                record.claim_b_id,
                record.warning_class.value,
                json.dumps(record.conditions_a),
                json.dumps(record.conditions_b),
                record.value_a,
                record.value_b,
                record.derivation_chain,
            ),
        )


def build_claim_fts_index(conn: sqlite3.Connection, claim_files: Sequence[LoadedClaimsFile]) -> None:
    """Build the FTS5 index over claim statements, conditions, and expressions."""
    for claim_file in claim_files:
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id
            if not isinstance(claim_id, str) or not claim_id:
                continue
            statement = claim.statement or ""
            expression = claim.expression or ""
            conditions = list(claim.conditions)
            conditions_text = " ".join(conditions)

            conn.execute(
                "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
                "VALUES (?, ?, ?, ?)",
                (claim_id, statement, conditions_text, expression),
            )

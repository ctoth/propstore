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
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from quire.references import FamilyReferenceIndex
from quire.projections import (
    FtsProjection,
    ProjectionRow,
)
from quire.sqlite_vec_store import embedding_status_projection, rowid_vec_projection
from propstore.claims import (
    ClaimFileEntry,
    claim_file_filename,
    claim_file_stage,
)
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.id_types import (
    ClaimId,
    to_claim_id,
    to_justification_id,
)
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.claims.storage import (
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_concept_link_rows,
    prepare_claim_insert_row,
)
from propstore.families.claims.stages import (
    ClaimSidecarRows,
    PromotionBlockedClaimFact,
    PromotionBlockedSidecarRows,
    RawIdQuarantineRecord,
    RawIdQuarantineSidecarRows,
)
from propstore.families.diagnostics.declaration import (
    BUILD_DIAGNOSTICS_PROJECTION,
    QuarantineDiagnostic,
    compile_promotion_blocked_diagnostic_rows,
    delete_promotion_blocked_diagnostics,
)
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.relations.declaration import (
    CLAIM_STANCE_DISCRIMINATORS,
    CLAIM_STANCE_STORAGE_MODEL,
    CONFLICT_WITNESS_TABLE,
    RELATION_EDGE_TABLE,
    StanceRow,
)
from propstore.stances import coerce_stance_type

if TYPE_CHECKING:
    from propstore.core.graph_types import ProvenanceRecord
    from propstore.core.justifications import CanonicalJustification


def _require_claim_type(value: object) -> ClaimType:
    claim_type = coerce_claim_type(value)
    if claim_type is None:
        raise KeyError('claim_type')
    return claim_type


from propstore.families.claims.projection_model import (  # noqa: E402
    CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL,
    CLAIM_ALGORITHM_PAYLOAD_TABLE,
    CLAIM_CONCEPT_LINK_TABLE,
    CLAIM_CORE_STORAGE_MODEL,
    CLAIM_CORE_TABLE,
    CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL,
    CLAIM_NUMERIC_PAYLOAD_TABLE,
    CLAIM_ROW_MODEL,
    CLAIM_TEXT_PAYLOAD_STORAGE_MODEL,
    CLAIM_TEXT_PAYLOAD_TABLE,
    JUSTIFICATION_TABLE,
    SOURCE_CHARTER_QUERY_TABLE,
    claim_row_query_plan,
)


def select_claim_rows(
    conn: sqlite3.Connection,
    where_sql: str = "",
    params: tuple[Any, ...] = (),
) -> list[ActiveClaim]:
    return list(
        CLAIM_ROW_MODEL.select_with_attached_rows(
            conn,
            CLAIM_ROW_QUERY_PLAN,
            where_sql,
            params,
        )
    )


def select_claim_rows_linked_to_concept(
    conn: sqlite3.Connection,
    concept_id: str | None,
    *,
    roles: tuple[str, ...] | None = None,
) -> list[ActiveClaim]:
    where_sql, params = _claim_concept_link_where_sql(concept_id, roles=roles)
    return select_claim_rows(conn, where_sql + "ORDER BY core.id", params)


def select_claim_rows_with_visibility(
    conn: sqlite3.Connection,
    *,
    concept_id: str | None,
    include_drafts: bool,
    include_blocked: bool,
) -> list[ActiveClaim]:
    clauses: list[str] = []
    bound: list[Any] = []
    concept_clause, concept_params = _claim_concept_link_where_sql(concept_id)
    if concept_clause:
        clauses.append(concept_clause.removeprefix("WHERE ").strip())
        bound.extend(concept_params)
    if not include_drafts:
        clauses.append("(core.stage IS NULL OR core.stage != 'draft')")
    if not include_blocked:
        clauses.append("(core.build_status IS NULL OR core.build_status != 'blocked')")
        clauses.append(
            "(core.promotion_status IS NULL OR core.promotion_status != 'blocked')"
        )
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses) + " "
    return select_claim_rows(conn, where_sql + "ORDER BY core.id", tuple(bound))


def _claim_concept_link_where_sql(
    concept_id: str | None,
    *,
    roles: tuple[str, ...] | None = None,
) -> tuple[str, tuple[Any, ...]]:
    if concept_id is None:
        return "", ()
    predicates = [
        "link.claim_id = core.id",
        "link.concept_id = ?",
    ]
    params: list[Any] = [concept_id]
    if roles:
        placeholders = ",".join("?" for _ in roles)
        predicates.append(f"link.role IN ({placeholders})")
        params.extend(roles)
    where_sql = (
        "WHERE EXISTS ("
        "SELECT 1 FROM claim_concept_link AS link "
        f"WHERE {' AND '.join(predicates)}"
        ") "
    )
    return where_sql, tuple(params)


def build_claim_logical_id_index(conn: sqlite3.Connection) -> dict[str, str]:
    index: dict[str, str] = {}
    rows = conn.execute(
        "SELECT id, primary_logical_id, logical_ids_json FROM claim_core"
    ).fetchall()
    for row in rows:
        artifact_id = row["id"]
        primary_logical_id = row["primary_logical_id"]
        if isinstance(primary_logical_id, str) and primary_logical_id:
            index.setdefault(primary_logical_id, artifact_id)
        logical_ids_json = row["logical_ids_json"]
        if not isinstance(logical_ids_json, str) or not logical_ids_json:
            continue
        try:
            logical_ids = json.loads(logical_ids_json)
        except json.JSONDecodeError:
            continue
        if not isinstance(logical_ids, list):
            continue
        for entry in logical_ids:
            if not isinstance(entry, dict):
                continue
            namespace = entry.get("namespace")
            value = entry.get("value")
            if isinstance(namespace, str) and isinstance(value, str):
                index.setdefault(f"{namespace}:{value}", artifact_id)
                index.setdefault(value, artifact_id)
    return index


def resolve_claim_id(
    conn: sqlite3.Connection,
    name: str,
    *,
    logical_id_index: Mapping[str, str] | None = None,
) -> str | None:
    row = conn.execute(
        "SELECT id FROM claim_core WHERE id = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return str(row["id"])

    row = conn.execute(
        "SELECT id FROM claim_core WHERE primary_logical_id = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return str(row["id"])

    return None if logical_id_index is None else logical_id_index.get(name)


def count_claims(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM claim_core").fetchone()[0])


def select_authored_justifications(
    conn: sqlite3.Connection,
) -> tuple[CanonicalJustification, ...]:
    rows = conn.execute(
        """
        SELECT id, justification_kind, conclusion_claim_id,
               premise_claim_ids, source_relation_type, source_claim_id,
               provenance_json, rule_strength
        FROM justification
        ORDER BY id
        """
    ).fetchall()
    return tuple(_canonical_justification_from_row(row) for row in rows)


def count_authored_justifications(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM justification").fetchone()[0])


def _canonical_justification_from_row(
    row: sqlite3.Row,
) -> CanonicalJustification:
    from propstore.core.justifications import CanonicalJustification

    justification_id = str(row["id"])
    premise_claim_ids = _decode_justification_premises(
        row["premise_claim_ids"],
        justification_id=justification_id,
    )
    provenance = _decode_justification_provenance(
        row["provenance_json"],
        justification_id=justification_id,
    )
    attributes = tuple(
        (key, row[key])
        for key in ("source_relation_type", "source_claim_id")
        if row[key] is not None
    )
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=str(row["conclusion_claim_id"]),
        premise_claim_ids=premise_claim_ids,
        rule_kind=str(row["justification_kind"]),
        rule_strength=str(row["rule_strength"] or "defeasible"),
        provenance=provenance,
        attributes=attributes,
    )


def _decode_justification_premises(
    value: object,
    *,
    justification_id: str,
) -> tuple[str, ...]:
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        raise ValueError(
            f"justification {justification_id!r} premise_claim_ids must decode to a list"
        )
    return tuple(str(item) for item in loaded)


def _decode_justification_provenance(
    value: object,
    *,
    justification_id: str,
) -> ProvenanceRecord | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must be JSON text"
        )
    loaded = json.loads(value)
    if not isinstance(loaded, Mapping):
        raise ValueError(
            f"justification {justification_id!r} provenance_json must decode to a mapping"
        )
    from propstore.core.graph_types import ProvenanceRecord

    return ProvenanceRecord.from_mapping(loaded)


def has_claim_core_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='claim_core'"
    ).fetchone()
    return row is not None


def delete_claim_core_row(conn: sqlite3.Connection, claim_id: str) -> None:
    conn.execute("DELETE FROM claim_core WHERE id = ?", (claim_id,))


def select_claim_embedding_rows(
    conn: sqlite3.Connection,
    entity_ids: Sequence[str] | None = None,
) -> list[ActiveClaim]:
    query = """
        SELECT
            core.id,
            core.id AS artifact_id,
            core.seq,
            core.content_hash,
            txt.auto_summary,
            txt.statement,
            txt.expression,
            txt.name
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
    """
    params: tuple[str, ...] = ()
    if entity_ids:
        placeholders = ",".join("?" for _ in entity_ids)
        query += f" WHERE core.id IN ({placeholders})"
        params = tuple(entity_ids)
    return [
        CLAIM_ROW_MODEL.from_row(dict(row))
        for row in conn.execute(query, params).fetchall()
    ]


def resolve_claim_embedding_entity(conn: sqlite3.Connection, entity_id: str) -> tuple[str, int]:
    row = conn.execute(
        "SELECT id, seq FROM claim_core WHERE id = ?",
        (entity_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Claim {entity_id} not found")
    return str(row["id"]), int(row["seq"])


def select_claim_text(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    rows = select_claim_texts(conn, [claim_id])
    return rows.get(claim_id)


def select_claim_texts(
    conn: sqlite3.Connection,
    claim_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    if not claim_ids:
        return {}
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT core.id, txt.auto_summary, txt.statement, txt.expression, core.source_paper
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        WHERE core.id IN ({placeholders})
        """,
        tuple(claim_ids),
    ).fetchall()
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        decoded = dict(row)
        decoded["text"] = (
            decoded.get("auto_summary")
            or decoded.get("statement")
            or decoded.get("expression")
            or decoded["id"]
        )
        result[str(decoded["id"])] = decoded
    return result


def select_all_claim_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id FROM claim_core").fetchall()
    return [str(row["id"]) for row in rows]


def select_source_promotion_claim_rows(
    conn: sqlite3.Connection,
    branch: str,
) -> tuple[tuple[str, str], ...]:
    rows = conn.execute(
        """
        SELECT id, promotion_status
        FROM claim_core
        WHERE branch = ? AND promotion_status IS NOT NULL
        ORDER BY id
        """,
        (branch,),
    ).fetchall()
    return tuple((str(row[0]), str(row[1])) for row in rows)


CLAIM_EMBEDDING_JOIN_SOURCE = """
    (
        SELECT
            core.id,
            core.seq,
            core.type,
            core.source_paper,
            COALESCE(output_link.concept_id, target_link.concept_id, core.target_concept) AS concept_id,
            txt.auto_summary,
            txt.statement
        FROM claim_core AS core
        LEFT JOIN claim_text_payload AS txt ON txt.claim_id = core.id
        LEFT JOIN claim_concept_link AS output_link
            ON output_link.claim_id = core.id AND output_link.role = 'output'
        LEFT JOIN claim_concept_link AS target_link
            ON target_link.claim_id = core.id AND target_link.role = 'target'
    )
"""


CLAIM_EMBEDDING_JOIN_COLUMNS = (
    "c.id, c.type, c.auto_summary, c.statement, c.source_paper, c.concept_id"
)


CLAIM_ROW_QUERY_PLAN = claim_row_query_plan(
    claim_core=CLAIM_CORE_TABLE,
    numeric_payload=CLAIM_NUMERIC_PAYLOAD_TABLE,
    text_payload=CLAIM_TEXT_PAYLOAD_TABLE,
    algorithm_payload=CLAIM_ALGORITHM_PAYLOAD_TABLE,
    source=SOURCE_CHARTER_QUERY_TABLE,
)


CLAIM_FTS_PROJECTION = FtsProjection(
    table="claim_fts",
    key_column="claim_id",
    columns=("statement", "conditions", "expression"),
    source_query="""
        SELECT
            c.id AS claim_id,
            COALESCE(t.statement, '') AS statement,
            COALESCE(
                (
                    SELECT group_concat(value, ' ')
                    FROM json_each(t.conditions_cel)
                ),
                ''
            ) AS conditions,
            COALESCE(t.expression, '') AS expression
        FROM claim_core c
        JOIN claim_text_payload t ON t.claim_id = c.id
        ORDER BY c.seq
    """,
)


CLAIM_EMBEDDING_STATUS_PROJECTION = embedding_status_projection(
    name="embedding_status",
    entity_id_column="claim_id",
    index_name="idx_embedding_status_model_identity",
)


CLAIM_VEC_PROJECTION = rowid_vec_projection("claim_vec_{model_identity_hash}")


def compile_claim_sidecar_rows(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: dict,
    *,
    form_registry: dict | None = None,
) -> ClaimSidecarRows:
    claim_seq = 0
    claim_core_rows: list[ProjectionRow] = []
    numeric_payload_rows: list[ProjectionRow] = []
    text_payload_rows: list[ProjectionRow] = []
    algorithm_payload_rows: list[ProjectionRow] = []
    claim_link_rows: list[ProjectionRow] = []
    stance_rows: list[ProjectionRow] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    claim_index = build_claim_file_reference_index(
        claim_bundle.normalized_claim_files
    )
    file_stage_by_filename: dict[str, str | None] = {
        claim_file_filename(claim_file): claim_file_stage(claim_file)
        for claim_file in claim_bundle.normalized_claim_files
    }

    for semantic_file in claim_bundle.semantic_files:
        file_stage = file_stage_by_filename.get(
            claim_file_filename(semantic_file.normalized_entry)
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
            claim_core_rows.append(CLAIM_CORE_TABLE.row(**CLAIM_CORE_STORAGE_MODEL.to_row(row)))
            numeric_payload_rows.append(
                CLAIM_NUMERIC_PAYLOAD_TABLE.row(**CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL.to_row(row))
            )
            text_payload_rows.append(
                CLAIM_TEXT_PAYLOAD_TABLE.row(**CLAIM_TEXT_PAYLOAD_STORAGE_MODEL.to_row(row))
            )
            algorithm_payload_rows.append(
                CLAIM_ALGORITHM_PAYLOAD_TABLE.row(**CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL.to_row(row))
            )
            for values in prepare_claim_concept_link_rows(semantic_claim):
                claim_link_rows.append(
                    CLAIM_CONCEPT_LINK_TABLE.row(
                        claim_id=values[0],
                        concept_id=values[1],
                        role=values[2],
                        ordinal=values[3],
                        binding_name=values[4],
                    )
                )
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_index,
                )
            )
            for values in deferred_stance_rows:
                stance_type = coerce_stance_type(values[2])
                if stance_type is None:
                    raise ValueError("deferred stance row requires a stance type")
                stance = StanceRow(
                    claim_id=to_claim_id(values[0]),
                    target_claim_id=to_claim_id(values[1]),
                    stance_type=stance_type,
                    target_justification_id=(
                        None if values[3] is None else to_justification_id(values[3])
                    ),
                    strength=None if values[4] is None else str(values[4]),
                    conditions_differ=(
                        None
                        if values[5] is None
                        else str(
                            json.dumps(values[5])
                            if isinstance(values[5], list)
                            else values[5]
                        )
                    ),
                    note=None if values[6] is None else str(values[6]),
                    resolution_method=None if values[7] is None else str(values[7]),
                    resolution_model=None if values[8] is None else str(values[8]),
                    embedding_model=None if values[9] is None else str(values[9]),
                    embedding_distance=(
                        None if values[10] is None else float(values[10])
                    ),
                    pass_number=None if values[11] is None else int(values[11]),
                    confidence=None if values[12] is None else float(values[12]),
                    opinion_belief=None if values[13] is None else float(values[13]),
                    opinion_disbelief=(
                        None if values[14] is None else float(values[14])
                    ),
                    opinion_uncertainty=(
                        None if values[15] is None else float(values[15])
                    ),
                    opinion_base_rate=(
                        None if values[16] is None else float(values[16])
                    ),
                    perspective_source_claim_id=(
                        None if values[17] is None else to_claim_id(values[17])
                    ),
                )
                row_values: dict[str, object] = {}
                for discriminator in CLAIM_STANCE_DISCRIMINATORS:
                    row_values.update(discriminator.row_values())
                row_values.update(CLAIM_STANCE_STORAGE_MODEL.to_row(stance))
                stance_rows.append(RELATION_EDGE_TABLE.row(**row_values))
            quarantine_diagnostics.extend(deferred_stance_diagnostics)

    return ClaimSidecarRows(
        claim_core_rows=tuple(claim_core_rows),
        numeric_payload_rows=tuple(numeric_payload_rows),
        text_payload_rows=tuple(text_payload_rows),
        algorithm_payload_rows=tuple(algorithm_payload_rows),
        claim_link_rows=tuple(claim_link_rows),
        stance_rows=tuple(stance_rows),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_authored_justification_sidecar_rows(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[ProjectionRow, ...]:
    rows, diagnostics = compile_authored_justification_sidecar_rows_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def compile_authored_justification_sidecar_rows_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[ProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification.to_payload()
        justification_id = justification.id
        conclusion = claim_index.resolve_id(justification.conclusion)
        if not isinstance(justification_id, str) or not justification_id:
            raise ValueError(
                f"justification artifact {filename} missing id"
            )
        if not isinstance(conclusion, str) or conclusion not in valid_claims:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent conclusion '{conclusion}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=conclusion or justification.conclusion or filename,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        resolved_premises: list[str] = []
        missing_premise_ref: str | None = None
        for premise in justification.premises:
            resolved_premise = claim_index.resolve_id(premise)
            if (
                not isinstance(resolved_premise, str)
                or resolved_premise not in valid_claims
            ):
                if isinstance(resolved_premise, str) and resolved_premise:
                    missing_premise_ref = resolved_premise
                elif isinstance(premise, str) and premise:
                    missing_premise_ref = premise
                else:
                    missing_premise_ref = filename
                break
            resolved_premises.append(resolved_premise)
        if missing_premise_ref is not None:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent premise '{missing_premise_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_premise_ref,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        provenance = justification_payload.get("provenance")
        attack_target = justification_payload.get("attack_target")
        provenance_payload: dict[str, object] = {}
        if isinstance(provenance, dict):
            provenance_payload.update(provenance)
        if isinstance(attack_target, dict):
            provenance_payload["attack_target"] = attack_target

        rows.append(
            JUSTIFICATION_TABLE.row(
                id=justification_id,
                justification_kind=str(justification.rule_kind or "reported_claim"),
                conclusion_claim_id=conclusion,
                premise_claim_ids=json.dumps(resolved_premises),
                source_relation_type=None,
                source_claim_id=None,
                provenance_json=json.dumps(provenance_payload)
                if provenance_payload
                else None,
                rule_strength=str(justification.rule_strength or "defeasible"),
            )
        )
    return tuple(rows), tuple(diagnostics)


def compile_raw_id_quarantine_sidecar_rows(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineSidecarRows:
    claim_rows: list[ProjectionRow] = []
    diagnostic_rows: list[ProjectionRow] = []

    for record in records:
        claim_rows.append(
            CLAIM_CORE_TABLE.row(
                id=record.synthetic_id,
                primary_logical_id="",
                logical_ids_json="[]",
                version_id="",
                content_hash="",
                seq=record.seq,
                type="quarantine",
                target_concept=None,
                source_slug=record.source_paper,
                source_paper=record.source_paper,
                provenance_page=0,
                provenance_json=None,
                context_id=None,
                premise_kind="ordinary",
                branch=None,
                build_status="blocked",
                stage=None,
                promotion_status=None,
            )
        )
        diagnostic_rows.append(
            BUILD_DIAGNOSTICS_PROJECTION.row(
                claim_id=record.synthetic_id,
                source_kind="claim",
                source_ref=record.raw_id,
                diagnostic_kind="raw_id_input",
                severity="error",
                blocking=1,
                message=record.message,
                file=record.filename,
                detail_json=record.detail_json,
            )
        )

    return RawIdQuarantineSidecarRows(
        claim_rows=tuple(claim_rows),
        diagnostic_rows=tuple(diagnostic_rows),
    )


def compile_promotion_blocked_claim_core_rows(
    facts: Sequence[PromotionBlockedClaimFact],
) -> tuple[ProjectionRow, ...]:
    return tuple(
        CLAIM_CORE_TABLE.row(
            id=fact.artifact_id,
            primary_logical_id="",
            logical_ids_json="[]",
            version_id="",
            content_hash="",
            seq=0,
            type="promotion_blocked",
            target_concept=None,
            source_slug=fact.source_paper,
            source_paper=fact.source_paper,
            provenance_page=0,
            provenance_json=None,
            context_id=None,
            premise_kind="ordinary",
            branch=fact.source_branch,
            build_status="ingested",
            stage=None,
            promotion_status="blocked",
        )
        for fact in facts
    )


def compile_promotion_blocked_sidecar_rows(
    facts: Sequence[PromotionBlockedClaimFact],
) -> PromotionBlockedSidecarRows:
    return PromotionBlockedSidecarRows(
        claim_rows=compile_promotion_blocked_claim_core_rows(facts),
        diagnostic_rows=compile_promotion_blocked_diagnostic_rows(facts),
    )


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ProjectionRow, ...]:
    conflict_claims = conflict_claims_from_claim_files(claim_files)
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    records.extend(
        detect_transitive_conflicts(
            conflict_claims,
            concept_registry,
            lifting_system=lifting_system,
        )
    )
    return tuple(
        CONFLICT_WITNESS_TABLE.row(
            concept_id=record.concept_id,
            claim_a_id=record.claim_a_id,
            claim_b_id=record.claim_b_id,
            warning_class=record.warning_class.value,
            conditions_a=json.dumps(record.conditions_a),
            conditions_b=json.dumps(record.conditions_b),
            value_a=record.value_a,
            value_b=record.value_b,
            derivation_chain=record.derivation_chain,
        )
        for record in records
    )


def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    CLAIM_CORE_TABLE.insert_rows(conn, (row.values for row in rows.claim_rows))
    for row in rows.diagnostic_rows:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(conn, row)


def populate_promotion_blocked_claims(
    conn: sqlite3.Connection,
    claim_rows: Sequence[ProjectionRow],
    diagnostic_rows: Sequence[ProjectionRow],
) -> None:
    if not claim_rows and not diagnostic_rows:
        return
    child_claim_tables = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (
                  'claim_concept_link',
                  'claim_numeric_payload',
                  'claim_text_payload',
                  'claim_algorithm_payload',
                  'micropublication_claim'
              )
            """
        ).fetchall()
    }
    schema_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "concept" not in schema_tables:
        child_claim_tables.discard("claim_concept_link")
    claim_rows_by_id = {str(row.values["id"]): row for row in claim_rows}
    claim_ids = tuple(claim_rows_by_id)
    for claim_id in claim_ids:
        for table_name in (
            "claim_concept_link",
            "claim_numeric_payload",
            "claim_text_payload",
            "claim_algorithm_payload",
            "micropublication_claim",
        ):
            if table_name not in child_claim_tables:
                continue
            conn.execute(
                f"DELETE FROM {table_name} WHERE claim_id = ?",
                (claim_id,),
            )
        delete_claim_core_row(conn, claim_id)
        delete_promotion_blocked_diagnostics(conn, claim_id)
    CLAIM_CORE_TABLE.insert_rows(conn, (row.values for row in claim_rows_by_id.values()))
    for row in diagnostic_rows:
        BUILD_DIAGNOSTICS_PROJECTION.insert_row(conn, row)


def populate_claims(
    conn: sqlite3.Connection,
    rows: ClaimSidecarRows,
) -> None:
    """Populate normalized claim storage from compiled sidecar rows.

    Schema-v3 behavior (``reviews/2026-04-16-code-review/workstreams/
    ws-z-render-gates.md`` finding 3.2): the file-level ``stage`` marker
    (e.g. ``'draft'``) is threaded from the claim-file document onto each
    ``claim_core`` row. Drafts populate normally; render-policy filtering
    (phase 4) decides visibility.

    ``artifact_id is the logical id`` for a claim. ``version_id`` is the
    content identity. Duplicate rows with the same ``artifact_id`` and
    same ``version_id`` are idempotent; duplicate logical ids with
    different versions emit a blocking ``claim_version_conflict``
    diagnostic instead of silently taking the first writer.
    """

    from propstore.families.relations.declaration import RELATION_EDGE_TABLE

    seen_claim_versions: dict[str, str] = {}
    emitted_conflicts: set[tuple[str, str, str]] = set()
    payloads_by_claim_id = {
        numeric_row.values["claim_id"]: (numeric_row, text_row, algorithm_row)
        for numeric_row, text_row, algorithm_row in zip(
            rows.numeric_payload_rows,
            rows.text_payload_rows,
            rows.algorithm_payload_rows,
            strict=True,
        )
    }
    for row in rows.claim_core_rows:
        claim_id = row.values.get("id")
        version_id = row.values.get("version_id")
        if isinstance(claim_id, str) and claim_id in seen_claim_versions:
            existing_version = seen_claim_versions[claim_id]
            new_version = str(version_id or "")
            if existing_version == new_version:
                continue
            conflict_key = (claim_id, existing_version, new_version)
            if conflict_key not in emitted_conflicts:
                _insert_claim_version_conflict(
                    conn,
                    claim_id=claim_id,
                    existing_version=existing_version,
                    new_version=new_version,
                    source_ref=str(row.values.get("primary_logical_id") or claim_id),
                )
                emitted_conflicts.add(conflict_key)
            continue
        CLAIM_CORE_TABLE.insert_row(conn, row.values)
        numeric_row, text_row, algorithm_row = payloads_by_claim_id[claim_id]
        CLAIM_NUMERIC_PAYLOAD_TABLE.insert_row(conn, numeric_row.values)
        CLAIM_TEXT_PAYLOAD_TABLE.insert_row(conn, text_row.values)
        CLAIM_ALGORITHM_PAYLOAD_TABLE.insert_row(conn, algorithm_row.values)
        if isinstance(claim_id, str):
            seen_claim_versions[claim_id] = str(version_id or "")
    seen_link_keys: set[tuple[object, object, object, object]] = set()
    for row in rows.claim_link_rows:
        key = (
            row.values["claim_id"],
            row.values["role"],
            row.values["ordinal"],
            row.values["concept_id"],
        )
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        CLAIM_CONCEPT_LINK_TABLE.insert_row(conn, row)
    if rows.stance_rows:
        RELATION_EDGE_TABLE.insert_rows(conn, (stance_row.values for stance_row in rows.stance_rows))


def _insert_claim_version_conflict(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    existing_version: str,
    new_version: str,
    source_ref: str,
) -> None:
    from propstore.families.diagnostics.declaration import BUILD_DIAGNOSTICS_PROJECTION

    BUILD_DIAGNOSTICS_PROJECTION.insert_row(
        conn,
        BUILD_DIAGNOSTICS_PROJECTION.row(
            claim_id=claim_id,
            source_kind="claim",
            source_ref=source_ref,
            diagnostic_kind="claim_version_conflict",
            severity="error",
            blocking=1,
            message=f"Claim logical id {claim_id!r} appears with multiple version_id values",
            file=None,
            detail_json=json.dumps(
                {
                    "existing_version_id": existing_version,
                    "new_version_id": new_version,
                },
                sort_keys=True,
            ),
        ),
    )


def populate_stances(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    from propstore.families.relations.declaration import RELATION_EDGE_TABLE

    RELATION_EDGE_TABLE.insert_rows(conn, (row.values for row in rows))


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    JUSTIFICATION_TABLE.insert_rows(conn, rows, or_ignore=True)


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ProjectionRow],
) -> None:
    CONFLICT_WITNESS_TABLE.insert_rows(conn, rows)

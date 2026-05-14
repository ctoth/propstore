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
from collections.abc import Mapping, Sequence

from dataclasses import dataclass

from propstore.sidecar.projection import (
    FtsProjection,
    ProjectionColumn,
    ProjectionForeignKey,
    ProjectionIndex,
    ProjectionTable,
)
from propstore.sidecar.claim_utils import normalize_conditions_differ
from propstore.sidecar.relations import RELATION_EDGE_PROJECTION
from propstore.sidecar.stages import (
    ClaimSidecarRows,
    RawIdQuarantineSidecarRows,
)

CLAIM_CORE_PROJECTION = ProjectionTable(
    name="claim_core",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("primary_logical_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("logical_ids_json", "TEXT", nullable=False, default_sql="'[]'"),
        ProjectionColumn("version_id", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("content_hash", "TEXT", nullable=False, default_sql="''"),
        ProjectionColumn("seq", "INTEGER", nullable=False),
        ProjectionColumn("type", "TEXT", nullable=False),
        ProjectionColumn("target_concept", "TEXT"),
        ProjectionColumn("source_slug", "TEXT"),
        ProjectionColumn("source_paper", "TEXT", nullable=False),
        ProjectionColumn("provenance_page", "INTEGER", nullable=False),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("context_id", "TEXT"),
        ProjectionColumn("premise_kind", "TEXT", nullable=False, default_sql="'ordinary'"),
        ProjectionColumn("branch", "TEXT"),
        ProjectionColumn("build_status", "TEXT", nullable=False, default_sql="'ingested'"),
        ProjectionColumn("stage", "TEXT"),
        ProjectionColumn("promotion_status", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("context_id",), "context", ("id",)),),
    indexes=(
        ProjectionIndex("idx_claim_core_target", ("target_concept",)),
        ProjectionIndex("idx_claim_core_type", ("type",)),
        ProjectionIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)),
        ProjectionIndex("idx_claim_core_build_status", ("build_status",)),
        ProjectionIndex("idx_claim_core_stage", ("stage",)),
        ProjectionIndex("idx_claim_core_promotion_status", ("promotion_status",)),
    ),
)


CLAIM_CONCEPT_LINK_PROJECTION = ProjectionTable(
    name="claim_concept_link",
    columns=(
        ProjectionColumn("claim_id", "TEXT", nullable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("role", "TEXT", nullable=False),
        ProjectionColumn("ordinal", "INTEGER", nullable=False),
        ProjectionColumn("binding_name", "TEXT"),
    ),
    primary_key=("claim_id", "role", "ordinal", "concept_id"),
    foreign_keys=(
        ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),
        ProjectionForeignKey(("concept_id",), "concept", ("id",)),
    ),
    indexes=(
        ProjectionIndex("idx_claim_concept_link_claim", ("claim_id",)),
        ProjectionIndex("idx_claim_concept_link_concept", ("concept_id",)),
        ProjectionIndex("idx_claim_concept_link_role", ("role",)),
    ),
)


CLAIM_NUMERIC_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_numeric_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("value", "REAL"),
        ProjectionColumn("lower_bound", "REAL"),
        ProjectionColumn("upper_bound", "REAL"),
        ProjectionColumn("uncertainty", "REAL"),
        ProjectionColumn("uncertainty_type", "TEXT"),
        ProjectionColumn("sample_size", "INTEGER"),
        ProjectionColumn("unit", "TEXT"),
        ProjectionColumn("value_si", "REAL"),
        ProjectionColumn("lower_bound_si", "REAL"),
        ProjectionColumn("upper_bound_si", "REAL"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_TEXT_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_text_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("conditions_cel", "TEXT"),
        ProjectionColumn("conditions_ir", "TEXT"),
        ProjectionColumn("statement", "TEXT"),
        ProjectionColumn("expression", "TEXT"),
        ProjectionColumn("sympy_generated", "TEXT"),
        ProjectionColumn("sympy_error", "TEXT"),
        ProjectionColumn("name", "TEXT"),
        ProjectionColumn("measure", "TEXT"),
        ProjectionColumn("listener_population", "TEXT"),
        ProjectionColumn("methodology", "TEXT"),
        ProjectionColumn("notes", "TEXT"),
        ProjectionColumn("description", "TEXT"),
        ProjectionColumn("auto_summary", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
)


CLAIM_ALGORITHM_PAYLOAD_PROJECTION = ProjectionTable(
    name="claim_algorithm_payload",
    columns=(
        ProjectionColumn("claim_id", "TEXT", primary_key=True),
        ProjectionColumn("body", "TEXT"),
        ProjectionColumn("canonical_ast", "TEXT"),
        ProjectionColumn("variables_json", "TEXT"),
        ProjectionColumn("algorithm_stage", "TEXT"),
    ),
    foreign_keys=(ProjectionForeignKey(("claim_id",), "claim_core", ("id",)),),
    indexes=(ProjectionIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
)


CONFLICT_WITNESS_PROJECTION = ProjectionTable(
    name="conflict_witness",
    columns=(
        ProjectionColumn("id", "INTEGER PRIMARY KEY AUTOINCREMENT", insertable=False),
        ProjectionColumn("concept_id", "TEXT", nullable=False),
        ProjectionColumn("claim_a_id", "TEXT", nullable=False),
        ProjectionColumn("claim_b_id", "TEXT", nullable=False),
        ProjectionColumn("warning_class", "TEXT", nullable=False),
        ProjectionColumn("conditions_a", "TEXT"),
        ProjectionColumn("conditions_b", "TEXT"),
        ProjectionColumn("value_a", "TEXT"),
        ProjectionColumn("value_b", "TEXT"),
        ProjectionColumn("derivation_chain", "TEXT"),
    ),
    indexes=(ProjectionIndex("idx_conflict_witness_concept", ("concept_id",)),),
)


JUSTIFICATION_PROJECTION = ProjectionTable(
    name="justification",
    columns=(
        ProjectionColumn("id", "TEXT", primary_key=True),
        ProjectionColumn("justification_kind", "TEXT", nullable=False),
        ProjectionColumn("conclusion_claim_id", "TEXT", nullable=False),
        ProjectionColumn("premise_claim_ids", "TEXT", nullable=False),
        ProjectionColumn("source_relation_type", "TEXT"),
        ProjectionColumn("source_claim_id", "TEXT"),
        ProjectionColumn("provenance_json", "TEXT"),
        ProjectionColumn("rule_strength", "TEXT", nullable=False, default_sql="'defeasible'"),
    ),
)


CLAIM_FTS_PROJECTION = FtsProjection(
    table="claim_fts",
    key_column="claim_id",
    columns=("statement", "conditions", "expression"),
    row_plan="compiled claim files",
)


@dataclass(frozen=True)
class ClaimCoreProjectionRow:
    values: Mapping[str, object]

    @classmethod
    def from_claim_mapping(cls, row: Mapping[str, object]) -> "ClaimCoreProjectionRow":
        return cls(
            {
                "id": row["id"],
                "primary_logical_id": row["primary_logical_id"],
                "logical_ids_json": row["logical_ids_json"],
                "version_id": row["version_id"],
                "content_hash": row.get("content_hash") or "",
                "seq": row["seq"],
                "type": row["type"],
                "target_concept": row["target_concept"],
                "source_slug": row["source_slug"],
                "source_paper": row["source_paper"],
                "provenance_page": row["provenance_page"],
                "provenance_json": row["provenance_json"],
                "context_id": row["context_id"],
                "premise_kind": row.get("premise_kind") or "ordinary",
                "branch": row.get("branch"),
                "build_status": row.get("build_status") or "ingested",
                "stage": row.get("stage"),
                "promotion_status": row.get("promotion_status"),
            }
        )

    def as_insert_mapping(self) -> Mapping[str, object]:
        return self.values


@dataclass(frozen=True)
class ClaimNumericPayloadProjectionRow:
    values: Mapping[str, object]

    @classmethod
    def from_claim_mapping(cls, row: Mapping[str, object]) -> "ClaimNumericPayloadProjectionRow":
        return cls(
            {
                "claim_id": row["id"],
                "value": row["value"],
                "lower_bound": row["lower_bound"],
                "upper_bound": row["upper_bound"],
                "uncertainty": row["uncertainty"],
                "uncertainty_type": row["uncertainty_type"],
                "sample_size": row["sample_size"],
                "unit": row["unit"],
                "value_si": row["value_si"],
                "lower_bound_si": row["lower_bound_si"],
                "upper_bound_si": row["upper_bound_si"],
            }
        )

    def as_insert_mapping(self) -> Mapping[str, object]:
        return self.values


@dataclass(frozen=True)
class ClaimTextPayloadProjectionRow:
    values: Mapping[str, object]

    @classmethod
    def from_claim_mapping(cls, row: Mapping[str, object]) -> "ClaimTextPayloadProjectionRow":
        return cls(
            {
                "claim_id": row["id"],
                "conditions_cel": row["conditions_cel"],
                "conditions_ir": row["conditions_ir"],
                "statement": row["statement"],
                "expression": row["expression"],
                "sympy_generated": row["sympy_generated"],
                "sympy_error": row["sympy_error"],
                "name": row["name"],
                "measure": row["measure"],
                "listener_population": row["listener_population"],
                "methodology": row["methodology"],
                "notes": row["notes"],
                "description": row["description"],
                "auto_summary": row["auto_summary"],
            }
        )

    def as_insert_mapping(self) -> Mapping[str, object]:
        return self.values


@dataclass(frozen=True)
class ClaimAlgorithmPayloadProjectionRow:
    values: Mapping[str, object]

    @classmethod
    def from_claim_mapping(cls, row: Mapping[str, object]) -> "ClaimAlgorithmPayloadProjectionRow":
        return cls(
            {
                "claim_id": row["id"],
                "body": row["body"],
                "canonical_ast": row["canonical_ast"],
                "variables_json": row["variables_json"],
                "algorithm_stage": row["algorithm_stage"],
            }
        )

    def as_insert_mapping(self) -> Mapping[str, object]:
        return self.values


@dataclass(frozen=True)
class ClaimConceptLinkProjectionRow:
    claim_id: object
    concept_id: object
    role: object
    ordinal: object
    binding_name: object

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "ClaimConceptLinkProjectionRow":
        return cls(*values)

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "claim_id": self.claim_id,
            "concept_id": self.concept_id,
            "role": self.role,
            "ordinal": self.ordinal,
            "binding_name": self.binding_name,
        }


@dataclass(frozen=True)
class ClaimStanceProjectionRow:
    values: Mapping[str, object]

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "ClaimStanceProjectionRow":
        return cls(
            {
                "source_kind": "claim",
                "source_id": values[0],
                "relation_type": values[2],
                "target_kind": "claim",
                "target_id": values[1],
                "perspective_source_claim_id": values[17],
                "target_justification_id": values[3],
                "conditions_cel": None,
                "strength": values[4],
                "conditions_differ": normalize_conditions_differ(values[5]),
                "note": values[6],
                "resolution_method": values[7],
                "resolution_model": values[8],
                "embedding_model": values[9],
                "embedding_distance": values[10],
                "pass_number": values[11],
                "confidence": values[12],
                "opinion_belief": values[13],
                "opinion_disbelief": values[14],
                "opinion_uncertainty": values[15],
                "opinion_base_rate": values[16],
            }
        )

    def as_insert_mapping(self) -> Mapping[str, object]:
        return self.values


@dataclass(frozen=True)
class JustificationProjectionRow:
    id: object
    justification_kind: object
    conclusion_claim_id: object
    premise_claim_ids: object
    source_relation_type: object
    source_claim_id: object
    provenance_json: object
    rule_strength: object

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "JustificationProjectionRow":
        return cls(*values)

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "id": self.id,
            "justification_kind": self.justification_kind,
            "conclusion_claim_id": self.conclusion_claim_id,
            "premise_claim_ids": self.premise_claim_ids,
            "source_relation_type": self.source_relation_type,
            "source_claim_id": self.source_claim_id,
            "provenance_json": self.provenance_json,
            "rule_strength": self.rule_strength,
        }


@dataclass(frozen=True)
class ConflictWitnessProjectionRow:
    concept_id: object
    claim_a_id: object
    claim_b_id: object
    warning_class: object
    conditions_a: object
    conditions_b: object
    value_a: object
    value_b: object
    derivation_chain: object

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "ConflictWitnessProjectionRow":
        return cls(*values)

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "concept_id": self.concept_id,
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
            "warning_class": self.warning_class,
            "conditions_a": self.conditions_a,
            "conditions_b": self.conditions_b,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "derivation_chain": self.derivation_chain,
        }


@dataclass(frozen=True)
class ClaimFtsProjectionRow:
    claim_id: object
    statement: object
    conditions: object
    expression: object

    @classmethod
    def from_values(cls, values: tuple[object, ...]) -> "ClaimFtsProjectionRow":
        return cls(*values)

    def as_insert_mapping(self) -> Mapping[str, object]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "conditions": self.conditions,
            "expression": self.expression,
        }



def populate_raw_id_quarantine_records(
    conn: sqlite3.Connection,
    rows: RawIdQuarantineSidecarRows,
) -> None:
    claim_core_insert_sql = CLAIM_CORE_PROJECTION.insert_sql()
    for row in rows.claim_rows:
        conn.execute(claim_core_insert_sql, row.as_insert_mapping())
    for row in rows.diagnostic_rows:
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row.values,
        )


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

    seen_claim_versions: dict[str, str] = {}
    emitted_conflicts: set[tuple[str, str, str]] = set()
    claim_core_insert_sql = CLAIM_CORE_PROJECTION.insert_sql()
    numeric_payload_insert_sql = CLAIM_NUMERIC_PAYLOAD_PROJECTION.insert_sql()
    text_payload_insert_sql = CLAIM_TEXT_PAYLOAD_PROJECTION.insert_sql()
    algorithm_payload_insert_sql = CLAIM_ALGORITHM_PAYLOAD_PROJECTION.insert_sql()
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
        conn.execute(claim_core_insert_sql, row.as_insert_mapping())
        numeric_row, text_row, algorithm_row = payloads_by_claim_id[claim_id]
        conn.execute(numeric_payload_insert_sql, numeric_row.as_insert_mapping())
        conn.execute(text_payload_insert_sql, text_row.as_insert_mapping())
        conn.execute(algorithm_payload_insert_sql, algorithm_row.as_insert_mapping())
        if isinstance(claim_id, str):
            seen_claim_versions[claim_id] = str(version_id or "")
    seen_link_keys: set[tuple[object, object, object, object]] = set()
    claim_link_insert_sql = CLAIM_CONCEPT_LINK_PROJECTION.insert_sql()
    for row in rows.claim_link_rows:
        key = (row.claim_id, row.role, row.ordinal, row.concept_id)
        if key in seen_link_keys:
            continue
        seen_link_keys.add(key)
        conn.execute(claim_link_insert_sql, row.as_insert_mapping())
    relation_edge_insert_sql = RELATION_EDGE_PROJECTION.insert_sql()
    for stance_row in rows.stance_rows:
        conn.execute(relation_edge_insert_sql, stance_row.as_insert_mapping())


def _insert_claim_version_conflict(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    existing_version: str,
    new_version: str,
    source_ref: str,
) -> None:
    conn.execute(
        """
        INSERT INTO build_diagnostics (
            claim_id, source_kind, source_ref, diagnostic_kind,
            severity, blocking, message, file, detail_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            "claim",
            source_ref,
            "claim_version_conflict",
            "error",
            1,
            f"Claim logical id {claim_id!r} appears with multiple version_id values",
            None,
            json.dumps(
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
    rows: Sequence[ClaimStanceProjectionRow],
) -> None:
    insert_sql = RELATION_EDGE_PROJECTION.insert_sql()
    for row in rows:
        conn.execute(insert_sql, row.as_insert_mapping())


def populate_authored_justifications(
    conn: sqlite3.Connection,
    rows: Sequence[JustificationProjectionRow],
) -> None:
    insert_sql = JUSTIFICATION_PROJECTION.insert_sql(or_ignore=True)
    for row in rows:
        conn.execute(insert_sql, row.as_insert_mapping())


def populate_conflicts(
    conn: sqlite3.Connection,
    rows: Sequence[ConflictWitnessProjectionRow],
) -> None:
    insert_sql = CONFLICT_WITNESS_PROJECTION.insert_sql()
    for row in rows:
        conn.execute(insert_sql, row.as_insert_mapping())


def populate_claim_fts_rows(
    conn: sqlite3.Connection,
    rows: Sequence[ClaimFtsProjectionRow],
) -> None:
    insert_sql = CLAIM_FTS_PROJECTION.insert_sql()
    for row in rows:
        conn.execute(insert_sql, row.as_insert_mapping())

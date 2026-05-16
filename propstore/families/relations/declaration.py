"""Relation-edge projection, row, and read-model declarations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from quire.projections import (
    AUTOINCREMENT_ID_FIELD,
    CONDITIONS_CEL_FIELD,
    ProjectionIndex,
    ProjectionRow,
    ProjectionTable,
    family_reference_field,
    integer_field,
    real_field,
    text_field,
)
from quire.references import FamilyReferenceIndex

from propstore.conflict_detector.models import ConflictClass, coerce_conflict_class
from propstore.core.concept_relationship_types import (
    ConceptRelationshipType,
    coerce_concept_relationship_type,
)
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    JustificationId,
    to_claim_id,
    to_concept_id,
    to_justification_id,
)
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.claims.storage import (
    coerce_stance_resolution,
    normalize_conditions_differ,
    resolution_opinion_columns,
)
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.documents.stances import StanceDocument
from propstore.stances import StanceType, coerce_stance_type
from propstore.stances import VALID_STANCE_TYPES


def _require_concept_relationship_type(value: object) -> ConceptRelationshipType:
    relation_type = coerce_concept_relationship_type(value)
    if relation_type is None:
        raise KeyError("relation_type")
    return relation_type


def _require_stance_type(value: object) -> StanceType:
    stance_type = coerce_stance_type(value)
    if stance_type is None:
        raise KeyError("stance_type")
    return stance_type


@dataclass(frozen=True)
class RelationshipRow:
    source_id: str
    target_id: str
    relation_type: ConceptRelationshipType
    conditions_cel: str | None = None
    note: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relation_type",
            coerce_concept_relationship_type(self.relation_type),
        )
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> RelationshipRow:
        known = {"source_id", "target_id", "type", "relation_type", "conditions_cel", "note"}
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in known and value is not None
        }
        relation_type = row_map.get("relation_type", row_map.get("type"))
        if relation_type is None:
            raise KeyError("relation_type")
        return cls(
            source_id=str(row_map["source_id"]),
            target_id=str(row_map["target_id"]),
            relation_type=_require_concept_relationship_type(relation_type),
            conditions_cel=(
                None if row_map.get("conditions_cel") is None else str(row_map["conditions_cel"])
            ),
            note=None if row_map.get("note") is None else str(row_map["note"]),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.relation_type.value,
        }
        if self.conditions_cel is not None:
            data["conditions_cel"] = self.conditions_cel
        if self.note is not None:
            data["note"] = self.note
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class StanceRow:
    claim_id: ClaimId
    target_claim_id: ClaimId
    stance_type: StanceType
    target_justification_id: JustificationId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stance_type", coerce_stance_type(self.stance_type))
        object.__setattr__(self, "attributes", dict(self.attributes))

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> StanceRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"claim_id", "target_claim_id", "stance_type", "target_justification_id"}
            and value is not None
        }
        return cls(
            claim_id=to_claim_id(row_map["claim_id"]),
            target_claim_id=to_claim_id(row_map["target_claim_id"]),
            stance_type=_require_stance_type(row_map["stance_type"]),
            target_justification_id=(
                None
                if row_map.get("target_justification_id") is None
                else to_justification_id(row_map["target_justification_id"])
            ),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_id": self.claim_id,
            "target_claim_id": self.target_claim_id,
            "stance_type": self.stance_type.value,
        }
        if self.target_justification_id is not None:
            data["target_justification_id"] = self.target_justification_id
        data.update(self.attributes)
        return data


@dataclass(frozen=True)
class ConflictRow:
    claim_a_id: ClaimId
    claim_b_id: ClaimId
    concept_id: ConceptId | None = None
    warning_class: ConflictClass | None = None
    conflict_class: ConflictClass | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "warning_class", coerce_conflict_class(self.warning_class))
        object.__setattr__(self, "conflict_class", coerce_conflict_class(self.conflict_class))
        object.__setattr__(self, "attributes", dict(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
        }
        if self.concept_id is not None:
            data["concept_id"] = self.concept_id
        if self.warning_class is not None:
            data["warning_class"] = self.warning_class.value
        if self.conflict_class is not None:
            data["conflict_class"] = self.conflict_class.value
        data.update(self.attributes)
        return data

    @classmethod
    def from_mapping(cls, row_map: Mapping[str, Any]) -> ConflictRow:
        attributes = {
            str(key): value
            for key, value in row_map.items()
            if key not in {"claim_a_id", "claim_b_id", "concept_id", "warning_class", "conflict_class"}
            and value is not None
        }
        return cls(
            claim_a_id=to_claim_id(row_map["claim_a_id"]),
            claim_b_id=to_claim_id(row_map["claim_b_id"]),
            concept_id=(
                None
                if row_map.get("concept_id") is None
                else to_concept_id(row_map["concept_id"])
            ),
            warning_class=coerce_conflict_class(row_map.get("warning_class")),
            conflict_class=coerce_conflict_class(row_map.get("conflict_class")),
            attributes=attributes,
        )


RelationshipRowInput = RelationshipRow | Mapping[str, Any]
StanceRowInput = StanceRow | Mapping[str, Any]
ConflictRowInput = ConflictRow | Mapping[str, Any]


def coerce_relationship_row(row: RelationshipRowInput) -> RelationshipRow:
    if isinstance(row, RelationshipRow):
        return row
    return RelationshipRow.from_mapping(row)


def coerce_stance_row(row: StanceRowInput) -> StanceRow:
    if isinstance(row, StanceRow):
        return row
    return StanceRow.from_mapping(row)


def coerce_conflict_row(row: ConflictRowInput) -> ConflictRow:
    if isinstance(row, ConflictRow):
        return row
    return ConflictRow.from_mapping(row)


RELATION_EDGE_PROJECTION = ProjectionTable(
    name="relation_edge",
    columns=(
        AUTOINCREMENT_ID_FIELD.column(),
        text_field("source_kind", nullable=False).column(),
        text_field("source_id", nullable=False).column(),
        text_field("relation_type", nullable=False).column(),
        text_field("target_kind", nullable=False).column(),
        text_field("target_id", nullable=False).column(),
        family_reference_field("claim", role="perspective_source").column(),
        family_reference_field("justification", role="target").column(),
        CONDITIONS_CEL_FIELD.column(),
        text_field("strength").column(),
        text_field("conditions_differ").column(),
        text_field("note").column(),
        text_field("resolution_method").column(),
        text_field("resolution_model").column(),
        text_field("embedding_model").column(),
        real_field("embedding_distance").column(),
        integer_field("pass_number").column(),
        real_field("confidence").column(),
        real_field("opinion_belief").column(
            check_sql="opinion_belief >= 0 AND opinion_belief <= 1"
        ),
        real_field("opinion_disbelief").column(
            check_sql="opinion_disbelief >= 0 AND opinion_disbelief <= 1"
        ),
        real_field("opinion_uncertainty").column(
            check_sql="opinion_uncertainty >= 0 AND opinion_uncertainty <= 1"
        ),
        real_field("opinion_base_rate").column(
            check_sql="opinion_base_rate > 0 AND opinion_base_rate < 1"
        ),
    ),
    checks=(
        "opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6",
    ),
    indexes=(
        ProjectionIndex("idx_relation_edge_source", ("source_kind", "source_id")),
        ProjectionIndex("idx_relation_edge_target", ("target_kind", "target_id")),
        ProjectionIndex("idx_relation_edge_type", ("relation_type",)),
    ),
)


def claim_stance_projection_row(values: tuple[object, ...]) -> ProjectionRow:
    return RELATION_EDGE_PROJECTION.row(
        source_kind="claim",
        source_id=values[0],
        relation_type=values[2],
        target_kind="claim",
        target_id=values[1],
        perspective_source_claim_id=values[17],
        target_justification_id=values[3],
        conditions_cel=None,
        strength=values[4],
        conditions_differ=normalize_conditions_differ(values[5]),
        note=values[6],
        resolution_method=values[7],
        resolution_model=values[8],
        embedding_model=values[9],
        embedding_distance=values[10],
        pass_number=values[11],
        confidence=values[12],
        opinion_belief=values[13],
        opinion_disbelief=values[14],
        opinion_uncertainty=values[15],
        opinion_base_rate=values[16],
    )


def compile_authored_stance_sidecar_rows(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[ProjectionRow, ...]:
    rows, diagnostics = compile_authored_stance_sidecar_rows_with_diagnostics(
        stance_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def compile_authored_stance_sidecar_rows_with_diagnostics(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[ProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, stance in stance_entries:
        source_claim = claim_index.resolve_id(stance.source_claim)
        if source_claim is None or source_claim not in valid_claims:
            missing_source = stance.source_claim or filename
            message = (
                f"stance artifact {filename} references nonexistent source claim "
                f"'{missing_source}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_source,
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        stance_payload = stance.to_payload()
        target = claim_index.resolve_id(stance.target or "")
        stance_type = stance_payload.get("type") or ""
        if target is None or target not in valid_claims:
            missing_target = stance.target or filename
            message = (
                f"stance artifact {filename} references nonexistent target claim "
                f"'{missing_target}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_target,
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        if stance_type not in VALID_STANCE_TYPES:
            raise ValueError(
                f"stance artifact {filename} uses unrecognized stance type "
                f"'{stance_type}'"
            )

        resolution = coerce_stance_resolution(
            stance_payload.get("resolution"),
            f"stance artifact {filename}",
        )
        opinion_columns = resolution_opinion_columns(resolution)
        perspective_source_claim = (
            claim_index.resolve_id(
                stance.perspective_source_claim_id or stance.source_claim
            )
            or source_claim
        )
        rows.append(
            claim_stance_projection_row(
                (
                    source_claim,
                    target,
                    stance_type,
                    stance.target_justification_id,
                    stance.strength,
                    stance.conditions_differ,
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
                    perspective_source_claim,
                )
            )
        )
    return tuple(rows), tuple(diagnostics)


STANCE_SELECT_COLUMNS = """
    source_id AS claim_id,
    target_id AS target_claim_id,
    relation_type AS stance_type,
    target_justification_id,
    strength,
    conditions_differ,
    note,
    resolution_method,
    resolution_model,
    embedding_model,
    embedding_distance,
    pass_number,
    confidence,
    opinion_belief,
    opinion_disbelief,
    opinion_uncertainty,
    opinion_base_rate
"""

STANCE_SELECT_COLUMNS_WITH_PERSPECTIVE = """
    source_id AS claim_id,
    target_id AS target_claim_id,
    relation_type AS stance_type,
    perspective_source_claim_id,
    target_justification_id,
    strength,
    conditions_differ,
    note,
    resolution_method,
    resolution_model,
    embedding_model,
    embedding_distance,
    pass_number,
    confidence,
    opinion_belief,
    opinion_disbelief,
    opinion_uncertainty,
    opinion_base_rate
"""


def select_stances_between(
    conn: sqlite3.Connection,
    claim_ids: set[str],
) -> list[StanceRow]:
    if not claim_ids:
        return []
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT {STANCE_SELECT_COLUMNS_WITH_PERSPECTIVE}
        FROM relation_edge
        WHERE source_kind = 'claim'
          AND target_kind = 'claim'
          AND source_id IN ({placeholders})
          AND target_id IN ({placeholders})
        """,  # noqa: S608
        list(claim_ids) + list(claim_ids),
    ).fetchall()
    return [StanceRow.from_mapping(dict(row)) for row in rows]


def select_conflicts(
    conn: sqlite3.Connection,
    concept_id: str | None = None,
) -> list[ConflictRow]:
    if concept_id is not None:
        rows = conn.execute(
            """
            SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                   conditions_a, conditions_b, value_a, value_b, derivation_chain
            FROM conflict_witness WHERE concept_id = ?
            """,
            (concept_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT concept_id, claim_a_id, claim_b_id, warning_class,
                   conditions_a, conditions_b, value_a, value_b, derivation_chain
            FROM conflict_witness
            """
        ).fetchall()
    return [ConflictRow.from_mapping(dict(row)) for row in rows]


def select_all_relationships(conn: sqlite3.Connection) -> list[RelationshipRow]:
    rows = conn.execute(
        """
        SELECT source_id, relation_type AS type, target_id, conditions_cel, note
        FROM relation_edge
        WHERE source_kind = 'concept' AND target_kind = 'concept'
        """
    ).fetchall()
    return [RelationshipRow.from_mapping(dict(row)) for row in rows]


def select_all_claim_stances(conn: sqlite3.Connection) -> list[StanceRow]:
    rows = conn.execute(
        f"""
        SELECT {STANCE_SELECT_COLUMNS}
        FROM relation_edge
        WHERE source_kind = 'claim' AND target_kind = 'claim'
        """
    ).fetchall()
    return [StanceRow.from_mapping(dict(row)) for row in rows]


def select_claim_stances_with_policy(
    conn: sqlite3.Connection,
    focus_claim_id: str,
    *,
    source_predicates: Sequence[str],
    source_params: Sequence[Any],
    target_predicates: Sequence[str],
    target_params: Sequence[Any],
) -> list[StanceRow]:
    predicates = [
        "edge.source_kind = 'claim'",
        "edge.target_kind = 'claim'",
        "(edge.source_id = ? OR edge.target_id = ?)",
        *source_predicates,
        *target_predicates,
    ]
    params: list[Any] = [
        focus_claim_id,
        focus_claim_id,
        *source_params,
        *target_params,
    ]
    rows = conn.execute(
        f"""
        SELECT
            edge.source_id AS claim_id,
            edge.target_id AS target_claim_id,
            edge.relation_type AS stance_type,
            edge.perspective_source_claim_id,
            edge.target_justification_id,
            edge.strength,
            edge.conditions_differ,
            edge.note,
            edge.resolution_method,
            edge.resolution_model,
            edge.embedding_model,
            edge.embedding_distance,
            edge.pass_number,
            edge.confidence,
            edge.opinion_belief,
            edge.opinion_disbelief,
            edge.opinion_uncertainty,
            edge.opinion_base_rate
        FROM relation_edge AS edge
        JOIN claim_core AS source_core ON source_core.id = edge.source_id
        JOIN claim_core AS target_core ON target_core.id = edge.target_id
        WHERE {' AND '.join(predicates)}
        """,  # noqa: S608
        tuple(params),
    ).fetchall()
    return [StanceRow.from_mapping(dict(row)) for row in rows]


def select_explanation_stances(
    conn: sqlite3.Connection,
    claim_id: str,
) -> list[StanceRow]:
    result: list[StanceRow] = []
    queue = [claim_id]
    visited = {claim_id}

    while queue:
        current = queue.pop(0)
        rows = conn.execute(
            f"""
            SELECT {STANCE_SELECT_COLUMNS}
            FROM relation_edge
            WHERE source_kind = 'claim' AND target_kind = 'claim' AND source_id = ?
            """,
            (current,),
        ).fetchall()
        for row in rows:
            stance = StanceRow.from_mapping(dict(row))
            result.append(stance)
            target = str(stance.target_claim_id)
            if target not in visited:
                visited.add(target)
                queue.append(target)

    return result


def count_conflicts(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM conflict_witness").fetchone()[0])

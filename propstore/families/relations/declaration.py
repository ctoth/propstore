"""Relation-edge projection, row, and read-model declarations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from quire.projections import ProjectionRow
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
from propstore.compiler.ir import SemanticClaim
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.documents.stances import StanceDocument
from propstore.stances import StanceType, coerce_stance_type
from propstore.stances import VALID_STANCE_TYPES


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

    def attribute_mapping(self) -> dict[str, Any]:
        data = dict(self.attributes)
        if self.conditions_cel is not None:
            data["conditions_cel"] = self.conditions_cel
        if self.note is not None:
            data["note"] = self.note
        return data


@dataclass(frozen=True)
class StanceRow:
    claim_id: ClaimId
    target_claim_id: ClaimId
    stance_type: StanceType
    target_justification_id: JustificationId | None = None
    perspective_source_claim_id: ClaimId | None = None
    strength: str | None = None
    conditions_differ: str | None = None
    note: str | None = None
    resolution_method: str | None = None
    resolution_model: str | None = None
    embedding_model: str | None = None
    embedding_distance: float | None = None
    pass_number: int | None = None
    confidence: float | None = None
    opinion_belief: float | None = None
    opinion_disbelief: float | None = None
    opinion_uncertainty: float | None = None
    opinion_base_rate: float | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stance_type", coerce_stance_type(self.stance_type))
        if self.perspective_source_claim_id is not None:
            object.__setattr__(
                self,
                "perspective_source_claim_id",
                to_claim_id(self.perspective_source_claim_id),
            )
        object.__setattr__(self, "attributes", dict(self.attributes))

    def attribute_mapping(self) -> dict[str, Any]:
        data = dict(self.attributes)
        for key in (
            "perspective_source_claim_id",
            "target_justification_id",
            "strength",
            "conditions_differ",
            "note",
            "resolution_method",
            "resolution_model",
            "embedding_model",
            "embedding_distance",
            "pass_number",
            "confidence",
            "opinion_belief",
            "opinion_disbelief",
            "opinion_uncertainty",
            "opinion_base_rate",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    def attribute_value(self, key: str) -> Any:
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None:
                return value
        return dict(self.attributes).get(key)


@dataclass(frozen=True)
class ConflictRow:
    claim_a_id: ClaimId
    claim_b_id: ClaimId
    concept_id: ConceptId | None = None
    warning_class: ConflictClass | None = None
    conflict_class: ConflictClass | None = None
    conditions_a: str | None = None
    conditions_b: str | None = None
    value_a: Any = None
    value_b: Any = None
    derivation_chain: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "warning_class", coerce_conflict_class(self.warning_class))
        object.__setattr__(self, "conflict_class", coerce_conflict_class(self.conflict_class))
        object.__setattr__(self, "attributes", dict(self.attributes))

    def attribute_mapping(self) -> dict[str, Any]:
        data = dict(self.attributes)
        for key in (
            "conditions_a",
            "conditions_b",
            "value_a",
            "value_b",
            "derivation_chain",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data


RelationshipRowInput = RelationshipRow | Mapping[str, Any]
StanceRowInput = StanceRow | Mapping[str, Any]
ConflictRowInput = ConflictRow | Mapping[str, Any]


def _optional_numeric(value: object, *, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, str | int | float):
        raise TypeError(f"{field} must be numeric")
    return float(value)


def _stance_resolution_payload(
    resolution: object,
    owner: str,
) -> dict[str, object]:
    if resolution is None:
        return {}
    if not isinstance(resolution, dict):
        raise ValueError(f"{owner} resolution must be a mapping")
    return resolution


def _resolution_opinion_columns(
    resolution: dict[str, object],
) -> tuple[object, object, object, object]:
    opinion = resolution.get("opinion")
    if opinion is None:
        return None, None, None, None
    if not isinstance(opinion, dict):
        raise ValueError("resolution opinion must be a mapping")
    return (
        opinion.get("b"),
        opinion.get("d"),
        opinion.get("u"),
        opinion.get("a"),
    )


def compile_claim_embedded_stance_rows_with_diagnostics(
    claim: SemanticClaim,
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[list[tuple], tuple[QuarantineDiagnostic, ...]]:
    claim_id = claim.artifact_id or claim.resolved_claim.artifact_id or claim.resolved_claim.id
    rows: list[tuple] = []
    diagnostics: list[QuarantineDiagnostic] = []
    valid_claim_ids = set(claim_index.ids())
    for stance in claim.stances:
        stance_type = stance.data.get("type")
        target_claim_id = stance.target_ref.resolved_id or stance.target_ref.raw_text
        if not target_claim_id or not stance_type:
            continue
        if stance_type not in VALID_STANCE_TYPES:
            message = (
                f"claim '{claim_id}' uses unrecognized stance type "
                f"'{stance_type}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=str(claim_id or target_claim_id),
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=claim.filename,
                )
            )
            continue
        if target_claim_id not in valid_claim_ids:
            message = (
                f"claim '{claim_id}' references nonexistent target claim "
                f"'{target_claim_id}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=str(target_claim_id),
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=claim.filename,
                )
            )
            continue
        resolution = _stance_resolution_payload(
            stance.data.get("resolution"),
            f"claim '{claim_id}' stance targeting '{target_claim_id}'",
        )
        opinion_columns = _resolution_opinion_columns(resolution)
        rows.append((
            claim_id,
            target_claim_id,
            stance_type,
            stance.data.get("target_justification_id"),
            stance.data.get("strength"),
            stance.data.get("conditions_differ"),
            stance.data.get("note"),
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
            claim_id,
        ))
    return rows, tuple(diagnostics)


from propstore.families.relations.projection_model import (  # noqa: E402
    CLAIM_STANCE_DISCRIMINATORS,
    CLAIM_STANCE_QUERY_PLAN,
    CLAIM_STANCE_STORAGE_MODEL,
    CLAIM_STANCE_WITH_PERSPECTIVE_QUERY_PLAN,
    CONFLICT_ROW_MODEL,
    CONFLICT_WITNESS_TABLE,
    CONCEPT_RELATIONSHIP_DISCRIMINATORS,
    CONCEPT_RELATIONSHIP_QUERY_PLAN,
    CONCEPT_RELATIONSHIP_STORAGE_MODEL,
    RELATION_EDGE_TABLE,
    RELATIONSHIP_ROW_MODEL,
    STANCE_ROW_MODEL,
)


def compile_claim_embedded_stance_sidecar_rows_with_diagnostics(
    claims: Iterable[SemanticClaim],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    rows: list[ProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []
    for claim in claims:
        embedded_rows, embedded_diagnostics = (
            compile_claim_embedded_stance_rows_with_diagnostics(
                claim,
                claim_index,
            )
        )
        rows.extend(_claim_embedded_stance_projection_row(values) for values in embedded_rows)
        diagnostics.extend(embedded_diagnostics)
    return tuple(rows), tuple(diagnostics)


def _claim_embedded_stance_projection_row(values: tuple) -> ProjectionRow:
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
            else str(json.dumps(values[5]) if isinstance(values[5], list) else values[5])
        ),
        note=None if values[6] is None else str(values[6]),
        resolution_method=None if values[7] is None else str(values[7]),
        resolution_model=None if values[8] is None else str(values[8]),
        embedding_model=None if values[9] is None else str(values[9]),
        embedding_distance=None if values[10] is None else float(values[10]),
        pass_number=None if values[11] is None else int(values[11]),
        confidence=None if values[12] is None else float(values[12]),
        opinion_belief=None if values[13] is None else float(values[13]),
        opinion_disbelief=None if values[14] is None else float(values[14]),
        opinion_uncertainty=None if values[15] is None else float(values[15]),
        opinion_base_rate=None if values[16] is None else float(values[16]),
        perspective_source_claim_id=(
            None if values[17] is None else to_claim_id(values[17])
        ),
    )
    row_values: dict[str, object] = {}
    for discriminator in CLAIM_STANCE_DISCRIMINATORS:
        row_values.update(discriminator.row_values())
    row_values.update(CLAIM_STANCE_STORAGE_MODEL.to_row(stance))
    return RELATION_EDGE_TABLE.row(**row_values)


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
        validated_stance_type = coerce_stance_type(stance_type)
        if validated_stance_type is None:
            raise ValueError(
                f"stance artifact {filename} uses unrecognized stance type "
                f"'{stance_type}'"
            )

        resolution = _stance_resolution_payload(
            stance_payload.get("resolution"),
            f"stance artifact {filename}",
        )
        opinion_columns = _resolution_opinion_columns(resolution)
        perspective_source_claim = (
            claim_index.resolve_id(
                stance.perspective_source_claim_id or stance.source_claim
            )
            or source_claim
        )
        embedding_distance = resolution.get("embedding_distance")
        pass_number = resolution.get("pass_number")
        confidence = resolution.get("confidence")
        if embedding_distance is not None and not isinstance(
            embedding_distance,
            str | int | float,
        ):
            raise TypeError("resolution embedding_distance must be numeric")
        if pass_number is not None and not isinstance(pass_number, str | int):
            raise TypeError("resolution pass_number must be an integer")
        if confidence is not None and not isinstance(confidence, str | int | float):
            raise TypeError("resolution confidence must be numeric")
        (
            raw_opinion_belief,
            raw_opinion_disbelief,
            raw_opinion_uncertainty,
            raw_opinion_base_rate,
        ) = opinion_columns
        opinion_belief = _optional_numeric(
            raw_opinion_belief,
            field="resolution opinion belief",
        )
        opinion_disbelief = _optional_numeric(
            raw_opinion_disbelief,
            field="resolution opinion disbelief",
        )
        opinion_uncertainty = _optional_numeric(
            raw_opinion_uncertainty,
            field="resolution opinion uncertainty",
        )
        opinion_base_rate = _optional_numeric(
            raw_opinion_base_rate,
            field="resolution opinion base rate",
        )
        stance_row = StanceRow(
            claim_id=to_claim_id(source_claim),
            target_claim_id=to_claim_id(target),
            stance_type=validated_stance_type,
            target_justification_id=(
                None
                if stance.target_justification_id is None
                else to_justification_id(stance.target_justification_id)
            ),
            strength=stance.strength,
            conditions_differ=(
                None
                if stance.conditions_differ is None
                else str(
                    json.dumps(stance.conditions_differ)
                    if isinstance(stance.conditions_differ, list)
                    else stance.conditions_differ
                )
            ),
            note=stance.note,
            resolution_method=(
                None if resolution.get("method") is None else str(resolution["method"])
            ),
            resolution_model=(
                None if resolution.get("model") is None else str(resolution["model"])
            ),
            embedding_model=(
                None
                if resolution.get("embedding_model") is None
                else str(resolution["embedding_model"])
            ),
            embedding_distance=(
                None if embedding_distance is None else float(embedding_distance)
            ),
            pass_number=(
                None if pass_number is None else int(pass_number)
            ),
            confidence=(
                None if confidence is None else float(confidence)
            ),
            opinion_belief=opinion_belief,
            opinion_disbelief=opinion_disbelief,
            opinion_uncertainty=opinion_uncertainty,
            opinion_base_rate=opinion_base_rate,
            perspective_source_claim_id=to_claim_id(perspective_source_claim),
        )
        row_values: dict[str, object] = {}
        for discriminator in CLAIM_STANCE_DISCRIMINATORS:
            row_values.update(discriminator.row_values())
        row_values.update(CLAIM_STANCE_STORAGE_MODEL.to_row(stance_row))
        rows.append(RELATION_EDGE_TABLE.row(**row_values))
    return tuple(rows), tuple(diagnostics)


def select_stances_between(
    conn: sqlite3.Connection,
    claim_ids: set[str],
) -> list[StanceRow]:
    if not claim_ids:
        return []
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        CLAIM_STANCE_WITH_PERSPECTIVE_QUERY_PLAN.select_sql(
            f"WHERE edge.source_id IN ({placeholders}) "
            f"AND edge.target_id IN ({placeholders})"
        ),  # noqa: S608
        list(claim_ids) + list(claim_ids),
    ).fetchall()
    return [STANCE_ROW_MODEL.from_row(dict(row)) for row in rows]


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
    return [CONFLICT_ROW_MODEL.from_row(dict(row)) for row in rows]


def select_all_relationships(conn: sqlite3.Connection) -> list[RelationshipRow]:
    rows = conn.execute(
        CONCEPT_RELATIONSHIP_QUERY_PLAN.select_sql()
    ).fetchall()
    return [RELATIONSHIP_ROW_MODEL.from_row(dict(row)) for row in rows]


def select_all_claim_stances(conn: sqlite3.Connection) -> list[StanceRow]:
    rows = conn.execute(
        CLAIM_STANCE_QUERY_PLAN.select_sql()
    ).fetchall()
    return [STANCE_ROW_MODEL.from_row(dict(row)) for row in rows]


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
            CLAIM_STANCE_QUERY_PLAN.select_sql("WHERE edge.source_id = ?"),
            (current,),
        ).fetchall()
        for row in rows:
            stance = STANCE_ROW_MODEL.from_row(dict(row))
            result.append(stance)
            target = str(stance.target_claim_id)
            if target not in visited:
                visited.add(target)
                queue.append(target)

    return result


def count_conflicts(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM conflict_witness").fetchone()[0])

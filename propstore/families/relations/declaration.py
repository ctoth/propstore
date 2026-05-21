"""Relation-edge model declarations and relation-family semantics."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from quire.references import FamilyReferenceIndex

from propstore.claims import ClaimFileEntry
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.conflict_detector.models import ConflictClass
from propstore.core.concept_relationship_types import ConceptRelationshipType
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


class RelationEdge:
    def __init__(
        self,
        *,
        source_kind: str,
        source_id: str,
        relation_type: object,
        target_kind: str,
        target_id: str,
        id: int | None = None,
        perspective_source_claim_id: str | None = None,
        target_justification_id: str | None = None,
        conditions_cel: str | None = None,
        strength: str | None = None,
        conditions_differ: str | None = None,
        note: str | None = None,
        resolution_method: str | None = None,
        resolution_model: str | None = None,
        embedding_model: str | None = None,
        embedding_distance: float | None = None,
        pass_number: int | None = None,
        confidence: float | None = None,
        opinion_belief: float | None = None,
        opinion_disbelief: float | None = None,
        opinion_uncertainty: float | None = None,
        opinion_base_rate: float | None = None,
    ) -> None:
        self.id = id
        self.source_kind = source_kind
        self.source_id = source_id
        self.relation_type = str(relation_type)
        self.target_kind = target_kind
        self.target_id = target_id
        self.perspective_source_claim_id = perspective_source_claim_id
        self.target_justification_id = target_justification_id
        self.conditions_cel = conditions_cel
        self.strength = strength
        self.conditions_differ = conditions_differ
        self.note = note
        self.resolution_method = resolution_method
        self.resolution_model = resolution_model
        self.embedding_model = embedding_model
        self.embedding_distance = embedding_distance
        self.pass_number = pass_number
        self.confidence = confidence
        self.opinion_belief = opinion_belief
        self.opinion_disbelief = opinion_disbelief
        self.opinion_uncertainty = opinion_uncertainty
        self.opinion_base_rate = opinion_base_rate

    def attribute_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key in (
            "perspective_source_claim_id",
            "target_justification_id",
            "conditions_cel",
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
        return getattr(self, key, None)


class ConceptRelation(RelationEdge):
    def __init__(
        self,
        source_id: ConceptId | str,
        relation_type: ConceptRelationshipType | str,
        target_id: ConceptId | str,
        *,
        id: int | None = None,
        conditions_cel: str | None = None,
        note: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            source_kind="concept",
            source_id=str(source_id),
            relation_type=relation_type,
            target_kind="concept",
            target_id=str(target_id),
            conditions_cel=conditions_cel,
            note=note,
        )


class Stance(RelationEdge):
    def __init__(
        self,
        claim_id: ClaimId | str,
        target_claim_id: ClaimId | str,
        stance_type: StanceType | str,
        *,
        id: int | None = None,
        target_justification_id: JustificationId | str | None = None,
        perspective_source_claim_id: ClaimId | str | None = None,
        strength: str | None = None,
        conditions_differ: str | None = None,
        note: str | None = None,
        resolution_method: str | None = None,
        resolution_model: str | None = None,
        embedding_model: str | None = None,
        embedding_distance: float | None = None,
        pass_number: int | None = None,
        confidence: float | None = None,
        opinion_belief: float | None = None,
        opinion_disbelief: float | None = None,
        opinion_uncertainty: float | None = None,
        opinion_base_rate: float | None = None,
    ) -> None:
        super().__init__(
            id=id,
            source_kind="claim",
            source_id=str(claim_id),
            relation_type=stance_type,
            target_kind="claim",
            target_id=str(target_claim_id),
            target_justification_id=None if target_justification_id is None else str(target_justification_id),
            perspective_source_claim_id=None if perspective_source_claim_id is None else str(perspective_source_claim_id),
            strength=strength,
            conditions_differ=conditions_differ,
            note=note,
            resolution_method=resolution_method,
            resolution_model=resolution_model,
            embedding_model=embedding_model,
            embedding_distance=embedding_distance,
            pass_number=pass_number,
            confidence=confidence,
            opinion_belief=opinion_belief,
            opinion_disbelief=opinion_disbelief,
            opinion_uncertainty=opinion_uncertainty,
            opinion_base_rate=opinion_base_rate,
        )

    @property
    def claim_id(self) -> ClaimId:
        return to_claim_id(self.source_id)

    @property
    def target_claim_id(self) -> ClaimId:
        return to_claim_id(self.target_id)

    @property
    def stance_type(self) -> StanceType:
        stance_type = coerce_stance_type(self.relation_type)
        if stance_type is None:
            raise ValueError("stance requires relation_type")
        return stance_type


class ConflictWitness:
    def __init__(
        self,
        claim_a_id: ClaimId | str,
        claim_b_id: ClaimId | str,
        *,
        id: int | None = None,
        concept_id: ConceptId | str | None = None,
        warning_class: ConflictClass | str | None = None,
        conflict_class: ConflictClass | str | None = None,
        conditions_a: str | None = None,
        conditions_b: str | None = None,
        value_a: Any = None,
        value_b: Any = None,
        derivation_chain: str | None = None,
    ) -> None:
        self.id = id
        self.claim_a_id = str(claim_a_id)
        self.claim_b_id = str(claim_b_id)
        self.concept_id = None if concept_id is None else str(concept_id)
        self.warning_class = None if warning_class is None else str(warning_class)
        self.conflict_class = None if conflict_class is None else str(conflict_class)
        self.conditions_a = conditions_a
        self.conditions_b = conditions_b
        self.value_a = value_a
        self.value_b = value_b
        self.derivation_chain = derivation_chain

    def attribute_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key in ("conditions_a", "conditions_b", "value_a", "value_b", "derivation_chain"):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data


RelationEdgeInput = RelationEdge | Mapping[str, Any]
StanceInput = Stance | Mapping[str, Any]
ConceptRelationInput = ConceptRelation | Mapping[str, Any]
ConflictWitnessInput = ConflictWitness | Mapping[str, Any]


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


def compile_claim_embedded_stance_models_with_diagnostics(
    claim: SemanticClaim,
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    claim_id = claim.artifact_id or claim.resolved_claim.artifact_id or claim.resolved_claim.id
    rows: list[Stance] = []
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
        rows.append(
            Stance(
                claim_id=str(claim_id),
                target_claim_id=str(target_claim_id),
                stance_type=str(stance_type),
                target_justification_id=(
                    None
                    if stance.data.get("target_justification_id") is None
                    else str(stance.data["target_justification_id"])
                ),
                strength=None if stance.data.get("strength") is None else str(stance.data["strength"]),
                conditions_differ=(
                    None
                    if stance.data.get("conditions_differ") is None
                    else str(
                        json.dumps(stance.data["conditions_differ"])
                        if isinstance(stance.data["conditions_differ"], list)
                        else stance.data["conditions_differ"]
                    )
                ),
                note=None if stance.data.get("note") is None else str(stance.data["note"]),
                resolution_method=None if resolution.get("method") is None else str(resolution["method"]),
                resolution_model=None if resolution.get("model") is None else str(resolution["model"]),
                embedding_model=None if resolution.get("embedding_model") is None else str(resolution["embedding_model"]),
                embedding_distance=_optional_numeric(resolution.get("embedding_distance"), field="resolution embedding_distance"),
                pass_number=None if resolution.get("pass_number") is None else int(str(resolution["pass_number"])),
                confidence=_optional_numeric(resolution.get("confidence"), field="resolution confidence"),
                opinion_belief=_optional_numeric(opinion_columns[0], field="resolution opinion belief"),
                opinion_disbelief=_optional_numeric(opinion_columns[1], field="resolution opinion disbelief"),
                opinion_uncertainty=_optional_numeric(opinion_columns[2], field="resolution opinion uncertainty"),
                opinion_base_rate=_optional_numeric(opinion_columns[3], field="resolution opinion base rate"),
                perspective_source_claim_id=str(claim_id),
            )
        )
    return tuple(rows), tuple(diagnostics)


def compile_claim_embedded_stance_sidecar_rows_with_diagnostics(
    claims: Iterable[SemanticClaim],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    rows: list[Stance] = []
    diagnostics: list[QuarantineDiagnostic] = []
    for claim in claims:
        embedded_rows, embedded_diagnostics = (
            compile_claim_embedded_stance_models_with_diagnostics(
                claim,
                claim_index,
            )
        )
        rows.extend(embedded_rows)
        diagnostics.extend(embedded_diagnostics)
    return tuple(rows), tuple(diagnostics)


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ConflictWitness, ...]:
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
        ConflictWitness(
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


def compile_authored_stance_sidecar_rows(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[Stance, ...]:
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
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[Stance] = []
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
        stance_model = Stance(
            claim_id=str(source_claim),
            target_claim_id=str(target),
            stance_type=validated_stance_type,
            target_justification_id=(
                None
                if stance.target_justification_id is None
                else str(to_justification_id(stance.target_justification_id))
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
            perspective_source_claim_id=str(perspective_source_claim),
        )
        rows.append(stance_model)
    return tuple(rows), tuple(diagnostics)


def select_stances_between(
    conn: sqlite3.Connection,
    claim_ids: set[str],
) -> list[Stance]:
    if not claim_ids:
        return []
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT source_id, target_id, relation_type, target_justification_id,
               perspective_source_claim_id, strength, conditions_differ, note,
               resolution_method, resolution_model, embedding_model,
               embedding_distance, pass_number, confidence, opinion_belief,
               opinion_disbelief, opinion_uncertainty, opinion_base_rate
        FROM relation_edge
        WHERE source_kind = 'claim'
          AND target_kind = 'claim'
          AND source_id IN ({placeholders})
          AND target_id IN ({placeholders})
        """,  # noqa: S608
        list(claim_ids) + list(claim_ids),
    ).fetchall()
    return [_stance_from_mapping(dict(row)) for row in rows]


def select_conflicts(
    conn: sqlite3.Connection,
    concept_id: str | None = None,
) -> list[ConflictWitness]:
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
    return [_conflict_from_mapping(dict(row)) for row in rows]


def select_all_relationships(conn: sqlite3.Connection) -> list[ConceptRelation]:
    rows = conn.execute(
        """
        SELECT source_id, relation_type, target_id, conditions_cel, note
        FROM relation_edge
        WHERE source_kind = 'concept' AND target_kind = 'concept'
        """
    ).fetchall()
    return [_concept_relation_from_mapping(dict(row)) for row in rows]


def select_all_claim_stances(conn: sqlite3.Connection) -> list[Stance]:
    rows = conn.execute(
        """
        SELECT source_id, target_id, relation_type, target_justification_id,
               perspective_source_claim_id, strength, conditions_differ, note,
               resolution_method, resolution_model, embedding_model,
               embedding_distance, pass_number, confidence, opinion_belief,
               opinion_disbelief, opinion_uncertainty, opinion_base_rate
        FROM relation_edge
        WHERE source_kind = 'claim' AND target_kind = 'claim'
        """
    ).fetchall()
    return [_stance_from_mapping(dict(row)) for row in rows]


def select_explanation_stances(
    conn: sqlite3.Connection,
    claim_id: str,
) -> list[Stance]:
    result: list[Stance] = []
    queue = [claim_id]
    visited = {claim_id}

    while queue:
        current = queue.pop(0)
        rows = conn.execute(
            """
            SELECT source_id, target_id, relation_type, target_justification_id,
                   perspective_source_claim_id, strength, conditions_differ, note,
                   resolution_method, resolution_model, embedding_model,
                   embedding_distance, pass_number, confidence, opinion_belief,
                   opinion_disbelief, opinion_uncertainty, opinion_base_rate
            FROM relation_edge
            WHERE source_kind = 'claim' AND target_kind = 'claim' AND source_id = ?
            """,
            (current,),
        ).fetchall()
        for row in rows:
            stance = _stance_from_mapping(dict(row))
            result.append(stance)
            target = str(stance.target_claim_id)
            if target not in visited:
                visited.add(target)
                queue.append(target)

    return result


def count_conflicts(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM conflict_witness").fetchone()[0])


def _stance_from_mapping(row: Mapping[str, Any]) -> Stance:
    return Stance(
        claim_id=str(row["source_id"]),
        target_claim_id=str(row["target_id"]),
        stance_type=str(row["relation_type"]),
        target_justification_id=row.get("target_justification_id"),
        perspective_source_claim_id=row.get("perspective_source_claim_id"),
        strength=row.get("strength"),
        conditions_differ=row.get("conditions_differ"),
        note=row.get("note"),
        resolution_method=row.get("resolution_method"),
        resolution_model=row.get("resolution_model"),
        embedding_model=row.get("embedding_model"),
        embedding_distance=row.get("embedding_distance"),
        pass_number=row.get("pass_number"),
        confidence=row.get("confidence"),
        opinion_belief=row.get("opinion_belief"),
        opinion_disbelief=row.get("opinion_disbelief"),
        opinion_uncertainty=row.get("opinion_uncertainty"),
        opinion_base_rate=row.get("opinion_base_rate"),
    )


def _concept_relation_from_mapping(row: Mapping[str, Any]) -> ConceptRelation:
    return ConceptRelation(
        source_id=str(row["source_id"]),
        relation_type=str(row["relation_type"]),
        target_id=str(row["target_id"]),
        conditions_cel=row.get("conditions_cel"),
        note=row.get("note"),
    )


def _conflict_from_mapping(row: Mapping[str, Any]) -> ConflictWitness:
    return ConflictWitness(
        claim_a_id=str(row["claim_a_id"]),
        claim_b_id=str(row["claim_b_id"]),
        concept_id=row.get("concept_id"),
        warning_class=row.get("warning_class"),
        conditions_a=row.get("conditions_a"),
        conditions_b=row.get("conditions_b"),
        value_a=row.get("value_a"),
        value_b=row.get("value_b"),
        derivation_chain=row.get("derivation_chain"),
    )

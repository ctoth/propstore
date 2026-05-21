"""Relation-edge model declarations and relation-family semantics."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from typing import Any

from quire.references import FamilyReferenceIndex

from propstore.claims import ClaimFileEntry
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
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
from propstore.families.claims.documents import ResolutionDocument
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
        resolution: ResolutionDocument | None = None,
    ) -> None:
        if resolution is not None:
            resolution_method = resolution.method
            resolution_model = resolution.model
            embedding_model = resolution.embedding_model
            embedding_distance = (
                None
                if resolution.embedding_distance is None
                else float(resolution.embedding_distance)
            )
            pass_number = resolution.pass_number
            confidence = (
                None if resolution.confidence is None else float(resolution.confidence)
            )
            if resolution.opinion is not None:
                opinion_belief = float(resolution.opinion.b)
                opinion_disbelief = float(resolution.opinion.d)
                opinion_uncertainty = float(resolution.opinion.u)
                opinion_base_rate = float(resolution.opinion.a)
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
        warning_class: str | None = None,
        conflict_class: str | None = None,
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


RelationEdgeInput = RelationEdge
StanceInput = Stance
ConceptRelationInput = ConceptRelation
ConflictWitnessInput = ConflictWitness


def compile_claim_embedded_stance_models_with_diagnostics(
    claim: SemanticClaim,
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    claim_id = claim.artifact_id or claim.resolved_claim.artifact_id or claim.resolved_claim.id
    models: list[Stance] = []
    diagnostics: list[QuarantineDiagnostic] = []
    valid_claim_ids = set(claim_index.ids())
    for semantic_stance in claim.stances:
        stance = semantic_stance.document
        stance_type = stance.type
        target_claim_id = (
            semantic_stance.target_ref.resolved_id
            or semantic_stance.target_ref.raw_text
        )
        if not target_claim_id or not stance_type:
            continue
        if stance_type.value not in VALID_STANCE_TYPES:
            message = (
                f"claim '{claim_id}' uses unrecognized stance type "
                f"'{stance_type.value}'"
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
        models.append(
            Stance(
                claim_id=str(claim_id),
                target_claim_id=str(target_claim_id),
                stance_type=stance_type,
                target_justification_id=(
                    None
                    if stance.target_justification_id is None
                    else str(stance.target_justification_id)
                ),
                strength=stance.strength,
                conditions_differ=stance.conditions_differ,
                note=stance.note,
                resolution=stance.resolution,
                perspective_source_claim_id=str(claim_id),
            )
        )
    return tuple(models), tuple(diagnostics)


def compile_claim_embedded_stance_models_for_claims_with_diagnostics(
    claims: Iterable[SemanticClaim],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    models: list[Stance] = []
    diagnostics: list[QuarantineDiagnostic] = []
    for claim in claims:
        embedded_models, embedded_diagnostics = (
            compile_claim_embedded_stance_models_with_diagnostics(
                claim,
                claim_index,
            )
        )
        models.extend(embedded_models)
        diagnostics.extend(embedded_diagnostics)
    return tuple(models), tuple(diagnostics)


def compile_conflict_witness_models(
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


def compile_authored_stance_models_with_diagnostics(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Stance, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    models: list[Stance] = []
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

        target = claim_index.resolve_id(stance.target or "")
        stance_type = stance.type
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
        if stance_type is None:
            raise ValueError(f"stance artifact {filename} requires a stance type")
        if stance_type.value not in VALID_STANCE_TYPES:
            raise ValueError(
                f"stance artifact {filename} uses unrecognized stance type "
                f"'{stance_type.value}'"
            )
        perspective_source_claim = (
            claim_index.resolve_id(
                stance.perspective_source_claim_id or stance.source_claim
            )
            or source_claim
        )
        stance_model = Stance(
            claim_id=str(source_claim),
            target_claim_id=str(target),
            stance_type=stance_type,
            target_justification_id=(
                None
                if stance.target_justification_id is None
                else str(to_justification_id(stance.target_justification_id))
            ),
            strength=stance.strength,
            conditions_differ=stance.conditions_differ,
            note=stance.note,
            resolution=stance.resolution,
            perspective_source_claim_id=str(perspective_source_claim),
        )
        models.append(stance_model)
    return tuple(models), tuple(diagnostics)

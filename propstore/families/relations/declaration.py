"""Relation-edge model declarations and relation-family semantics."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from typing import Any

from quire.charters import FamilyModel
from quire.references import FamilyReferenceIndex

from propstore.claims import ClaimFileEntry
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.core.id_types import (
    ClaimId,
    to_claim_id,
    to_justification_id,
)
from propstore.compiler.ir import SemanticClaim
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.claims.documents import ResolutionDocument
from propstore.families.documents.stances import StanceDocument
from propstore.stances import StanceType, coerce_stance_type
from propstore.stances import VALID_STANCE_TYPES


class RelationEdge(FamilyModel):
    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and _public_model_attrs(self) == _public_model_attrs(other)
        )

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
            value = getattr(self, key, None)
            if value is not None:
                data[key] = value
        return data

    def attribute_value(self, key: str) -> Any:
        return getattr(self, key, None)


def _public_model_attrs(model: object) -> dict[str, Any]:
    return {
        key: value
        for key, value in vars(model).items()
        if not key.startswith("_")
    }


class ConceptRelation(RelationEdge):
    pass


class Stance(RelationEdge):
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


class ConflictWitness(FamilyModel):
    def attribute_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key in ("conditions_a", "conditions_b", "value_a", "value_b", "derivation_chain"):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data


def _resolution_attributes(resolution: ResolutionDocument | None) -> dict[str, object]:
    if resolution is None:
        return {}
    attributes: dict[str, object] = {
        "resolution_method": resolution.method,
        "resolution_model": resolution.model,
        "embedding_model": resolution.embedding_model,
        "embedding_distance": (
            None
            if resolution.embedding_distance is None
            else float(resolution.embedding_distance)
        ),
        "pass_number": resolution.pass_number,
        "confidence": None if resolution.confidence is None else float(resolution.confidence),
    }
    if resolution.opinion is not None:
        attributes.update(
            opinion_belief=float(resolution.opinion.b),
            opinion_disbelief=float(resolution.opinion.d),
            opinion_uncertainty=float(resolution.opinion.u),
            opinion_base_rate=float(resolution.opinion.a),
        )
    return {key: value for key, value in attributes.items() if value is not None}


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
                source_kind="claim",
                source_id=str(claim_id),
                relation_type=str(stance_type),
                target_kind="claim",
                target_id=str(target_claim_id),
                target_justification_id=(
                    None
                    if stance.target_justification_id is None
                    else str(stance.target_justification_id)
                ),
                strength=stance.strength,
                conditions_differ=stance.conditions_differ,
                note=stance.note,
                perspective_source_claim_id=str(claim_id),
                **_resolution_attributes(stance.resolution),
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
            concept_id=str(record.concept_id),
            claim_a_id=str(record.claim_a_id),
            claim_b_id=str(record.claim_b_id),
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
            source_kind="claim",
            source_id=str(source_claim),
            relation_type=str(stance_type),
            target_kind="claim",
            target_id=str(target),
            target_justification_id=(
                None
                if stance.target_justification_id is None
                else str(to_justification_id(stance.target_justification_id))
            ),
            strength=stance.strength,
            conditions_differ=stance.conditions_differ,
            note=stance.note,
            perspective_source_claim_id=str(perspective_source_claim),
            **_resolution_attributes(stance.resolution),
        )
        models.append(stance_model)
    return tuple(models), tuple(diagnostics)

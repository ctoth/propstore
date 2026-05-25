"""Relation-edge model declarations and relation-family semantics."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, cast

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import (
    CharterField,
    CharterIndex,
    CharterPolymorphicModel,
    FamilyCharter,
    FamilyModel,
)
from quire.families import FamilyDefinition
from quire.references import FamilyReferenceIndex

from propstore.claims import LoadedClaimsFile
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.core.id_types import (
    ClaimId,
    JustificationId,
)
from propstore.core.diagnostics import QuarantineDiagnostic
from propstore.compiler.ir import SemanticClaim
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.claims.declaration import ResolutionDocument
from propstore.families.stances.declaration import StanceDocument
from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION
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
        return ClaimId(self.source_id)

    @property
    def target_claim_id(self) -> ClaimId:
        return ClaimId(self.target_id)

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


RELATIONS_CHARTERS: tuple[FamilyCharter, FamilyCharter] = (
        FamilyCharter(
            family=FamilyDefinition(
                key="relation_edge",
                name="relation_edge",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-relation_edge",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=RelationEdge,
                    placement=FlatYamlPlacement(".derived/relation_edge", str),
                ),
                identity_field="id",
            ),
            model=RelationEdge,
            fields=(
                CharterField("id", int, primary_key=True, nullable=False, generated=True),
                CharterField("source_kind", str, nullable=False),
                CharterField("source_id", str, nullable=False),
                CharterField("relation_type", str, nullable=False),
                CharterField("target_kind", str, nullable=False),
                CharterField("target_id", str, nullable=False),
                CharterField("perspective_source_claim_id", str),
                CharterField("target_justification_id", str),
                CharterField("conditions_cel", str),
                CharterField("strength", str),
                CharterField("conditions_differ", str),
                CharterField("note", str),
                CharterField("resolution_method", str),
                CharterField("resolution_model", str),
                CharterField("embedding_model", str),
                CharterField("embedding_distance", float),
                CharterField("pass_number", int),
                CharterField("confidence", float),
                CharterField("opinion_belief", float),
                CharterField("opinion_disbelief", float),
                CharterField("opinion_uncertainty", float),
                CharterField("opinion_base_rate", float),
            ),
            indexes=(
                CharterIndex("idx_relation_edge_source", ("source_kind", "source_id")),
                CharterIndex("idx_relation_edge_target", ("target_kind", "target_id")),
                CharterIndex("idx_relation_edge_type", ("relation_type",)),
            ),
            polymorphic_on="source_kind",
            polymorphic_identity="edge",
            polymorphic_models=(
                CharterPolymorphicModel(Stance, "claim"),
                CharterPolymorphicModel(ConceptRelation, "concept"),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="conflict_witness",
                name="conflict_witness",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-conflict_witness",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ConflictWitness,
                    placement=FlatYamlPlacement(".derived/conflict_witness", str),
                ),
                identity_field="id",
            ),
            model=ConflictWitness,
            fields=(
                CharterField("id", int, primary_key=True, nullable=False, generated=True),
                CharterField("claim_a_id", str, nullable=False),
                CharterField("claim_b_id", str, nullable=False),
                CharterField("concept_id", str, nullable=False),
                CharterField("warning_class", str, nullable=False),
                CharterField("conditions_a", str),
                CharterField("conditions_b", str),
                CharterField("value_a", str),
                CharterField("value_b", str),
                CharterField("derivation_chain", str),
            ),
            indexes=(CharterIndex("idx_conflict_witness_concept", ("concept_id",)),),
            semantic_metadata={"semantic": "propstore.world"},
        ),
    )


def _resolution_value(resolution: ResolutionDocument | Mapping[str, object], field: str) -> object:
    if isinstance(resolution, Mapping):
        return resolution.get(field)
    return getattr(resolution, field)


def _resolution_attributes(resolution: ResolutionDocument | Mapping[str, object] | None) -> dict[str, object]:
    if resolution is None:
        return {}
    opinion = _resolution_value(resolution, "opinion")
    embedding_distance = _resolution_value(resolution, "embedding_distance")
    confidence = _resolution_value(resolution, "confidence")
    attributes: dict[str, object] = {
        "resolution_method": _resolution_value(resolution, "method"),
        "resolution_model": _resolution_value(resolution, "model"),
        "embedding_model": _resolution_value(resolution, "embedding_model"),
        "embedding_distance": (
            None
            if embedding_distance is None
            else float(cast(float | int | str, embedding_distance))
        ),
        "pass_number": _resolution_value(resolution, "pass_number"),
        "confidence": (
            None
            if confidence is None
            else float(cast(float | int | str, confidence))
        ),
    }
    if opinion is not None:
        if isinstance(opinion, Mapping):
            attributes.update(
                opinion_belief=float(cast(float | int | str, opinion["b"])),
                opinion_disbelief=float(cast(float | int | str, opinion["d"])),
                opinion_uncertainty=float(cast(float | int | str, opinion["u"])),
                opinion_base_rate=float(cast(float | int | str, opinion["a"])),
            )
        else:
            opinion_obj = cast(Any, opinion)
            attributes.update(
                opinion_belief=float(opinion_obj.b),
                opinion_disbelief=float(opinion_obj.d),
                opinion_uncertainty=float(opinion_obj.u),
                opinion_base_rate=float(opinion_obj.a),
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
    claim_files: Sequence[LoadedClaimsFile],
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
                else str(JustificationId(stance.target_justification_id))
            ),
            strength=stance.strength,
            conditions_differ=stance.conditions_differ,
            note=stance.note,
            perspective_source_claim_id=str(perspective_source_claim),
            **_resolution_attributes(stance.resolution),
        )
        models.append(stance_model)
    return tuple(models), tuple(diagnostics)

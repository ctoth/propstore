"""Typed source-local document models."""

from __future__ import annotations

from typing import Any

from propstore.families.claims.documents import (
    ClaimLogicalIdDocument,
    ClaimSourceDocument,
    FitStatisticsDocument,
    ParameterBindingDocument,
    ResolutionDocument,
    StanceDocument,
    VariableBindingDocument,
)
from propstore.cel_types import CelExpr
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.core.claim_types import ClaimType
from propstore.core.exactness_types import Exactness
from propstore.core.source_types import SourceKind, SourceOriginType
from quire.documents import DocumentStruct
from propstore.opinion import Opinion
from propstore.provenance import ProvenanceStatus
from propstore.stances import StanceType


class SourceOriginDocument(DocumentStruct):
    type: SourceOriginType
    value: str
    retrieved: str | None = None
    content_ref: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type.value,
            "value": self.value,
        }
        if self.retrieved is not None:
            payload["retrieved"] = self.retrieved
        if self.content_ref is not None:
            payload["content_ref"] = self.content_ref
        return payload


class SourceTrustQualityDocument(DocumentStruct):
    status: ProvenanceStatus
    b: float | int
    d: float | int
    u: float | int
    a: float | int

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "b": self.b,
            "d": self.d,
            "u": self.u,
            "a": self.a,
        }


class SourceTrustDocument(DocumentStruct):
    status: ProvenanceStatus
    prior_base_rate: Opinion | None = None
    quality: SourceTrustQualityDocument | None = None
    derived_from: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.prior_base_rate is not None:
            payload["prior_base_rate"] = {
                "b": self.prior_base_rate.b,
                "d": self.prior_base_rate.d,
                "u": self.prior_base_rate.u,
                "a": self.prior_base_rate.a,
            }
        if self.quality is not None:
            payload["quality"] = self.quality.to_payload()
        if self.derived_from:
            payload["derived_from"] = list(self.derived_from)
        return payload


class SourceMetadataDocument(DocumentStruct):
    name: str

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name}


class SourceDocument(DocumentStruct):
    id: str
    kind: SourceKind
    origin: SourceOriginDocument
    trust: SourceTrustDocument
    metadata: SourceMetadataDocument | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind.value,
            "origin": self.origin.to_payload(),
            "trust": self.trust.to_payload(),
        }
        if self.metadata is not None:
            payload["metadata"] = self.metadata.to_payload()
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class SourceConceptAliasDocument(DocumentStruct):
    name: str
    source: str | None = None
    note: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": self.name}
        if self.source is not None:
            payload["source"] = self.source
        if self.note is not None:
            payload["note"] = self.note
        return payload


class SourceConceptRegistryMatchDocument(DocumentStruct):
    artifact_id: str
    canonical_name: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"artifact_id": self.artifact_id}
        if self.canonical_name is not None:
            payload["canonical_name"] = self.canonical_name
        return payload


class SourceConceptFormParametersDocument(DocumentStruct):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.construction is not None:
            payload["construction"] = self.construction
        if self.extensible is not None:
            payload["extensible"] = self.extensible
        if self.note is not None:
            payload["note"] = self.note
        if self.reference is not None:
            payload["reference"] = self.reference
        if self.values is not None:
            payload["values"] = list(self.values)
        return payload


class SourceParameterizationRelationshipDocument(DocumentStruct):
    inputs: tuple[str, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    source: str | None = None
    bidirectional: bool | None = None
    conditions: tuple[CelExpr, ...] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"inputs": list(self.inputs)}
        if self.formula is not None:
            payload["formula"] = self.formula
        if self.sympy is not None:
            payload["sympy"] = self.sympy
        if self.exactness is not None:
            payload["exactness"] = self.exactness.value
        if self.source is not None:
            payload["source"] = self.source
        if self.bidirectional is not None:
            payload["bidirectional"] = self.bidirectional
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.note is not None:
            payload["note"] = self.note
        if self.canonical_claim is not None:
            payload["canonical_claim"] = self.canonical_claim
        if self.fit_statistics is not None:
            payload["fit_statistics"] = self.fit_statistics
        return payload


class SourceConceptEntryDocument(DocumentStruct):
    local_name: str | None = None
    proposed_name: str | None = None
    definition: str | None = None
    form: str | None = None
    aliases: tuple[SourceConceptAliasDocument, ...] = ()
    form_parameters: SourceConceptFormParametersDocument | None = None
    parameterization_relationships: tuple[SourceParameterizationRelationshipDocument, ...] = ()
    status: str | None = None
    registry_match: SourceConceptRegistryMatchDocument | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.local_name is not None:
            payload["local_name"] = self.local_name
        if self.proposed_name is not None:
            payload["proposed_name"] = self.proposed_name
        if self.definition is not None:
            payload["definition"] = self.definition
        if self.form is not None:
            payload["form"] = self.form
        if self.aliases:
            payload["aliases"] = [alias.to_payload() for alias in self.aliases]
        if self.form_parameters is not None:
            payload["form_parameters"] = self.form_parameters.to_payload()
        if self.parameterization_relationships:
            payload["parameterization_relationships"] = [
                relationship.to_payload()
                for relationship in self.parameterization_relationships
            ]
        if self.status is not None:
            payload["status"] = self.status
        if self.registry_match is not None:
            payload["registry_match"] = self.registry_match.to_payload()
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class SourceConceptsDocument(DocumentStruct):
    concepts: tuple[SourceConceptEntryDocument, ...]

    def to_payload(self) -> dict[str, Any]:
        return {"concepts": [entry.to_payload() for entry in self.concepts]}


class SourceClaimDocument(DocumentStruct):
    artifact_id: str | None = None
    logical_ids: tuple[ClaimLogicalIdDocument, ...] = ()
    version_id: str | None = None
    type: ClaimType | None = None
    provenance: SourceProvenanceDocument | None = None
    id: str | None = None
    body: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    conditions: tuple[CelExpr, ...] = ()
    context: str | None = None
    equations: tuple[str, ...] = ()
    expression: str | None = None
    fit: FitStatisticsDocument | None = None
    listener_population: str | None = None
    lower_bound: float | int | None = None
    measure: str | None = None
    methodology: str | None = None
    name: str | None = None
    notes: str | None = None
    parameters: tuple[ParameterBindingDocument, ...] = ()
    sample_size: int | None = None
    stage: AlgorithmStage | None = None
    stances: tuple[StanceDocument, ...] = ()
    statement: str | None = None
    sympy: str | None = None
    target_concept: str | None = None
    uncertainty: float | int | None = None
    uncertainty_type: str | None = None
    unit: str | None = None
    upper_bound: float | int | None = None
    value: float | int | None = None
    variables: tuple[VariableBindingDocument, ...] = ()
    source_local_id: str | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.artifact_id is not None:
            payload["artifact_id"] = self.artifact_id
        if self.logical_ids:
            payload["logical_ids"] = [logical_id.to_payload() for logical_id in self.logical_ids]
        if self.version_id is not None:
            payload["version_id"] = self.version_id
        if self.type is not None:
            payload["type"] = self.type.value
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_payload()
        if self.id is not None:
            payload["id"] = self.id
        if self.body is not None:
            payload["body"] = self.body
        if self.concept is not None:
            payload["concept"] = self.concept
        if self.concepts:
            payload["concepts"] = list(self.concepts)
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.context is not None:
            payload["context"] = self.context
        if self.equations:
            payload["equations"] = list(self.equations)
        if self.expression is not None:
            payload["expression"] = self.expression
        if self.fit is not None:
            payload["fit"] = self.fit.to_payload()
        if self.listener_population is not None:
            payload["listener_population"] = self.listener_population
        if self.lower_bound is not None:
            payload["lower_bound"] = self.lower_bound
        if self.measure is not None:
            payload["measure"] = self.measure
        if self.methodology is not None:
            payload["methodology"] = self.methodology
        if self.name is not None:
            payload["name"] = self.name
        if self.notes is not None:
            payload["notes"] = self.notes
        if self.parameters:
            payload["parameters"] = [parameter.to_payload() for parameter in self.parameters]
        if self.sample_size is not None:
            payload["sample_size"] = self.sample_size
        if self.stage is not None:
            payload["stage"] = str(self.stage)
        if self.stances:
            payload["stances"] = [stance.to_payload() for stance in self.stances]
        if self.statement is not None:
            payload["statement"] = self.statement
        if self.sympy is not None:
            payload["sympy"] = self.sympy
        if self.target_concept is not None:
            payload["target_concept"] = self.target_concept
        if self.uncertainty is not None:
            payload["uncertainty"] = self.uncertainty
        if self.uncertainty_type is not None:
            payload["uncertainty_type"] = self.uncertainty_type
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.upper_bound is not None:
            payload["upper_bound"] = self.upper_bound
        if self.value is not None:
            payload["value"] = self.value
        if self.variables:
            payload["variables"] = [variable.to_payload() for variable in self.variables]
        if self.source_local_id is not None:
            payload["source_local_id"] = self.source_local_id
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class ExtractionProvenanceDocument(DocumentStruct):
    reader: str | None = None
    method: str | None = None
    timestamp: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.reader is not None:
            payload["reader"] = self.reader
        if self.method is not None:
            payload["method"] = self.method
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        return payload


class SourceClaimsDocument(DocumentStruct):
    claims: tuple[SourceClaimDocument, ...]
    source: ClaimSourceDocument | None = None
    produced_by: ExtractionProvenanceDocument | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"claims": [claim.to_payload() for claim in self.claims]}
        if self.source is not None:
            payload["source"] = self.source.to_payload()
        if self.produced_by is not None:
            payload["produced_by"] = self.produced_by.to_payload()
        return payload


class SourceAttackTargetDocument(DocumentStruct):
    target_claim: str | None = None
    target_justification_id: str | None = None
    target_premise_index: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.target_claim is not None:
            payload["target_claim"] = self.target_claim
        if self.target_justification_id is not None:
            payload["target_justification_id"] = self.target_justification_id
        if self.target_premise_index is not None:
            payload["target_premise_index"] = self.target_premise_index
        return payload


class SourceProvenanceDocument(DocumentStruct):
    paper: str | None = None
    page: int | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.paper is not None:
            payload["paper"] = self.paper
        if self.page is not None:
            payload["page"] = self.page
        if self.figure is not None:
            payload["figure"] = self.figure
        if self.quote_fragment is not None:
            payload["quote_fragment"] = self.quote_fragment
        if self.section is not None:
            payload["section"] = self.section
        if self.table is not None:
            payload["table"] = self.table
        return payload


class SourceJustificationDocument(DocumentStruct):
    id: str | None = None
    conclusion: str | None = None
    premises: tuple[str, ...] = ()
    rule_kind: str | None = None
    rule_strength: str | None = None
    provenance: SourceProvenanceDocument | None = None
    attack_target: SourceAttackTargetDocument | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.id is not None:
            payload["id"] = self.id
        if self.conclusion is not None:
            payload["conclusion"] = self.conclusion
        if self.premises:
            payload["premises"] = list(self.premises)
        if self.rule_kind is not None:
            payload["rule_kind"] = self.rule_kind
        if self.rule_strength is not None:
            payload["rule_strength"] = self.rule_strength
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_payload()
        if self.attack_target is not None:
            payload["attack_target"] = self.attack_target.to_payload()
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class SourceJustificationsDocument(DocumentStruct):
    justifications: tuple[SourceJustificationDocument, ...]
    source: ClaimSourceDocument | None = None
    produced_by: ExtractionProvenanceDocument | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "justifications": [
                justification.to_payload()
                for justification in self.justifications
            ]
        }
        if self.source is not None:
            payload["source"] = self.source.to_payload()
        if self.produced_by is not None:
            payload["produced_by"] = self.produced_by.to_payload()
        return payload


class SourceStanceEntryDocument(DocumentStruct):
    source_claim: str | None = None
    target: str | None = None
    type: StanceType | None = None
    strength: str | None = None
    note: str | None = None
    conditions_differ: str | None = None
    resolution: ResolutionDocument | None = None
    target_justification_id: str | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.source_claim is not None:
            payload["source_claim"] = self.source_claim
        if self.target is not None:
            payload["target"] = self.target
        if self.type is not None:
            payload["type"] = self.type.value
        if self.strength is not None:
            payload["strength"] = self.strength
        if self.note is not None:
            payload["note"] = self.note
        if self.conditions_differ is not None:
            payload["conditions_differ"] = self.conditions_differ
        if self.resolution is not None:
            payload["resolution"] = self.resolution.to_payload()
        if self.target_justification_id is not None:
            payload["target_justification_id"] = self.target_justification_id
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class SourceStancesDocument(DocumentStruct):
    stances: tuple[SourceStanceEntryDocument, ...]
    source: ClaimSourceDocument | None = None
    produced_by: ExtractionProvenanceDocument | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"stances": [stance.to_payload() for stance in self.stances]}
        if self.source is not None:
            payload["source"] = self.source.to_payload()
        if self.produced_by is not None:
            payload["produced_by"] = self.produced_by.to_payload()
        return payload


class SourceParameterizationGroupMergeDocument(DocumentStruct):
    merged_group: tuple[str, ...]
    previous_groups: tuple[tuple[str, ...], ...]
    introduced_by: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "merged_group": list(self.merged_group),
            "previous_groups": [list(group) for group in self.previous_groups],
            "introduced_by": list(self.introduced_by),
        }


class SourceFinalizeCalibrationDocument(DocumentStruct):
    prior_base_rate_status: str
    source_quality_status: str
    fallback_to_default_base_rate: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "prior_base_rate_status": self.prior_base_rate_status,
            "source_quality_status": self.source_quality_status,
            "fallback_to_default_base_rate": self.fallback_to_default_base_rate,
        }


class SourceFinalizeReportDocument(DocumentStruct):
    kind: str
    source: str
    status: str
    artifact_code_status: str
    calibration: SourceFinalizeCalibrationDocument
    micropub_status: str = "not_composed"
    claim_reference_errors: tuple[str, ...] = ()
    micropub_coverage_errors: tuple[str, ...] = ()
    justification_reference_errors: tuple[str, ...] = ()
    stance_reference_errors: tuple[str, ...] = ()
    concept_alignment_candidates: tuple[str, ...] = ()
    parameterization_group_merges: tuple[SourceParameterizationGroupMergeDocument, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "status": self.status,
            "claim_reference_errors": list(self.claim_reference_errors),
            "micropub_coverage_errors": list(self.micropub_coverage_errors),
            "justification_reference_errors": list(self.justification_reference_errors),
            "stance_reference_errors": list(self.stance_reference_errors),
            "concept_alignment_candidates": list(self.concept_alignment_candidates),
            "parameterization_group_merges": [
                merge.to_payload()
                for merge in self.parameterization_group_merges
            ],
            "artifact_code_status": self.artifact_code_status,
            "micropub_status": self.micropub_status,
            "calibration": self.calibration.to_payload(),
        }

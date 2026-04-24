"""Typed document models for canonical claim YAML files."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from propstore.cel_types import CelExpr
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.core.claim_concept_link_roles import ClaimConceptLinkRole
from propstore.core.claim_types import ClaimType
from quire.documents import DocumentStruct
from quire.versions import VersionId
from propstore.families.contexts.documents import ContextReferenceDocument
from propstore.provenance import Provenance
from propstore.stances import StanceType


CLAIM_TYPE_CONTRACT_VERSION = VersionId("2026.04.28")


@dataclass(frozen=True)
class ClaimConceptLinkDeclaration:
    field: str
    role: ClaimConceptLinkRole
    target_family: str = "concept"
    source: str = "scalar"
    message_subject: str | None = None

    def contract_body(self) -> dict[str, object]:
        return {
            "field": self.field,
            "role": self.role.value,
            "target_family": self.target_family,
            "source": self.source,
            "message_subject": self.message_subject,
        }


@dataclass(frozen=True)
class ClaimValueGroupDeclaration:
    value_field: str = "value"
    lower_bound_field: str = "lower_bound"
    upper_bound_field: str = "upper_bound"
    uncertainty_field: str = "uncertainty"
    uncertainty_type_field: str = "uncertainty_type"

    def contract_body(self) -> dict[str, object]:
        return {
            "value_field": self.value_field,
            "lower_bound_field": self.lower_bound_field,
            "upper_bound_field": self.upper_bound_field,
            "uncertainty_field": self.uncertainty_field,
            "uncertainty_type_field": self.uncertainty_type_field,
        }


@dataclass(frozen=True)
class ClaimUnitPolicyDeclaration:
    required: bool = True
    dimensionless_default_unit: str | None = None
    form_concept_field: str | None = None

    def contract_body(self) -> dict[str, object]:
        return {
            "required": self.required,
            "dimensionless_default_unit": self.dimensionless_default_unit,
            "form_concept_field": self.form_concept_field,
        }


class ClaimSemanticCheck:
    name: ClassVar[str]

    @classmethod
    def contract_body(cls) -> dict[str, str]:
        return {
            "name": cls.name,
            "class": f"{cls.__module__}.{cls.__qualname__}",
        }


class UnitFormCompatibilityCheck(ClaimSemanticCheck):
    name = "unit_form_compatibility"


class SympyGenerationCheck(ClaimSemanticCheck):
    name = "sympy_generation"


class DimensionalConsistencyCheck(ClaimSemanticCheck):
    name = "dimensional_consistency"


class AlgorithmParseCheck(ClaimSemanticCheck):
    name = "algorithm_parse"


class AlgorithmUnboundNamesCheck(ClaimSemanticCheck):
    name = "algorithm_unbound_names"


@dataclass(frozen=True)
class ClaimTypeContract:
    claim_type: ClaimType
    required_fields: tuple[str, ...] = ()
    nonempty_fields: tuple[str, ...] = ()
    concept_links: tuple[ClaimConceptLinkDeclaration, ...] = ()
    value_group: ClaimValueGroupDeclaration | None = None
    unit_policy: ClaimUnitPolicyDeclaration | None = None
    semantic_checks: tuple[type[ClaimSemanticCheck], ...] = ()
    contract_version: VersionId = CLAIM_TYPE_CONTRACT_VERSION

    def contract_body(self) -> dict[str, object]:
        return {
            "claim_type": self.claim_type.value,
            "required_fields": self.required_fields,
            "nonempty_fields": self.nonempty_fields,
            "concept_links": tuple(
                link.contract_body()
                for link in self.concept_links
            ),
            "value_group": (
                None
                if self.value_group is None
                else self.value_group.contract_body()
            ),
            "unit_policy": (
                None
                if self.unit_policy is None
                else self.unit_policy.contract_body()
            ),
            "semantic_checks": tuple(
                semantic_check.contract_body()
                for semantic_check in self.semantic_checks
            ),
        }


_ABOUT_CONCEPT_LINK = ClaimConceptLinkDeclaration(
    field="concepts",
    role=ClaimConceptLinkRole.ABOUT,
    source="list",
)
_VARIABLE_INPUT_LINK = ClaimConceptLinkDeclaration(
    field="variables",
    role=ClaimConceptLinkRole.INPUT,
    source="bindings",
    message_subject="variable",
)
_PARAMETER_INPUT_LINK = ClaimConceptLinkDeclaration(
    field="parameters",
    role=ClaimConceptLinkRole.INPUT,
    source="bindings",
    message_subject="parameter",
)
_VALUE_GROUP = ClaimValueGroupDeclaration()

CLAIM_TYPE_CONTRACTS: dict[ClaimType, ClaimTypeContract] = {
    ClaimType.PARAMETER: ClaimTypeContract(
        claim_type=ClaimType.PARAMETER,
        required_fields=("output_concept",),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="output_concept",
                role=ClaimConceptLinkRole.OUTPUT,
            ),
        ),
        value_group=_VALUE_GROUP,
        unit_policy=ClaimUnitPolicyDeclaration(
            dimensionless_default_unit="1",
            form_concept_field="output_concept",
        ),
        semantic_checks=(UnitFormCompatibilityCheck,),
    ),
    ClaimType.EQUATION: ClaimTypeContract(
        claim_type=ClaimType.EQUATION,
        required_fields=("expression",),
        nonempty_fields=("variables",),
        concept_links=(_VARIABLE_INPUT_LINK,),
        semantic_checks=(SympyGenerationCheck, DimensionalConsistencyCheck),
    ),
    ClaimType.OBSERVATION: ClaimTypeContract(
        claim_type=ClaimType.OBSERVATION,
        required_fields=("statement",),
        nonempty_fields=("concepts",),
        concept_links=(_ABOUT_CONCEPT_LINK,),
    ),
    ClaimType.MECHANISM: ClaimTypeContract(
        claim_type=ClaimType.MECHANISM,
        required_fields=("statement",),
        nonempty_fields=("concepts",),
        concept_links=(_ABOUT_CONCEPT_LINK,),
    ),
    ClaimType.COMPARISON: ClaimTypeContract(
        claim_type=ClaimType.COMPARISON,
        required_fields=("statement",),
        nonempty_fields=("concepts",),
        concept_links=(_ABOUT_CONCEPT_LINK,),
    ),
    ClaimType.LIMITATION: ClaimTypeContract(
        claim_type=ClaimType.LIMITATION,
        required_fields=("statement",),
        nonempty_fields=("concepts",),
        concept_links=(_ABOUT_CONCEPT_LINK,),
    ),
    ClaimType.MODEL: ClaimTypeContract(
        claim_type=ClaimType.MODEL,
        required_fields=("name",),
        nonempty_fields=("equations", "parameters"),
        concept_links=(_PARAMETER_INPUT_LINK,),
    ),
    ClaimType.MEASUREMENT: ClaimTypeContract(
        claim_type=ClaimType.MEASUREMENT,
        required_fields=("target_concept", "measure"),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="target_concept",
                role=ClaimConceptLinkRole.TARGET,
            ),
        ),
        value_group=_VALUE_GROUP,
        unit_policy=ClaimUnitPolicyDeclaration(),
    ),
    ClaimType.ALGORITHM: ClaimTypeContract(
        claim_type=ClaimType.ALGORITHM,
        required_fields=("body", "output_concept"),
        nonempty_fields=("variables",),
        concept_links=(
            ClaimConceptLinkDeclaration(
                field="output_concept",
                role=ClaimConceptLinkRole.OUTPUT,
            ),
            _VARIABLE_INPUT_LINK,
        ),
        semantic_checks=(AlgorithmParseCheck, AlgorithmUnboundNamesCheck),
    ),
}


def claim_type_contract_for(claim_type: object) -> ClaimTypeContract | None:
    try:
        normalized = ClaimType(str(claim_type))
    except ValueError:
        return None
    return CLAIM_TYPE_CONTRACTS.get(normalized)


def iter_claim_type_contracts() -> tuple[ClaimTypeContract, ...]:
    return tuple(
        CLAIM_TYPE_CONTRACTS[claim_type]
        for claim_type in sorted(CLAIM_TYPE_CONTRACTS, key=lambda item: item.value)
    )


class ClaimLogicalIdDocument(DocumentStruct):
    namespace: str
    value: str
    confidence: float | int | None = None
    pass_number: int | None = None

    @property
    def formatted(self) -> str:
        return f"{self.namespace}:{self.value}"

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "namespace": self.namespace,
            "value": self.value,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.pass_number is not None:
            payload["pass_number"] = self.pass_number
        return payload


class ClaimSourceDocument(DocumentStruct):
    paper: str
    extraction_date: str | None = None
    extraction_model: str | None = None
    extraction_prompt_hash: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"paper": self.paper}
        if self.extraction_date is not None:
            payload["extraction_date"] = self.extraction_date
        if self.extraction_model is not None:
            payload["extraction_model"] = self.extraction_model
        if self.extraction_prompt_hash is not None:
            payload["extraction_prompt_hash"] = self.extraction_prompt_hash
        return payload


class ProvenanceDocument(DocumentStruct):
    page: int
    paper: str | None = None
    date: str | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"page": self.page}
        if self.paper is not None:
            payload["paper"] = self.paper
        if self.date is not None:
            payload["date"] = self.date
        if self.figure is not None:
            payload["figure"] = self.figure
        if self.quote_fragment is not None:
            payload["quote_fragment"] = self.quote_fragment
        if self.section is not None:
            payload["section"] = self.section
        if self.table is not None:
            payload["table"] = self.table
        return payload


class FitStatisticsDocument(DocumentStruct):
    r: float | int | None = None
    r_sd: float | int | None = None
    slope: float | int | None = None
    slope_sd: float | int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.r is not None:
            payload["r"] = self.r
        if self.r_sd is not None:
            payload["r_sd"] = self.r_sd
        if self.slope is not None:
            payload["slope"] = self.slope
        if self.slope_sd is not None:
            payload["slope_sd"] = self.slope_sd
        return payload


class VariableBindingDocument(DocumentStruct):
    concept: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None

    @property
    def binding_name(self) -> str | None:
        if self.name is not None:
            return self.name
        return self.symbol

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"concept": self.concept}
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.role is not None:
            payload["role"] = self.role
        if self.name is not None:
            payload["name"] = self.name
        return payload


class ParameterBindingDocument(DocumentStruct):
    name: str
    concept: str
    note: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "concept": self.concept,
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload


class OpinionDocument(DocumentStruct):
    b: float | int
    d: float | int
    u: float | int
    a: float | int
    provenance: Provenance

    def __post_init__(self) -> None:
        for name, value in (("b", self.b), ("d", self.d), ("u", self.u)):
            if value < -1e-9 or value > 1.0 + 1e-9:
                raise ValueError(f"{name}={value} not in [0, 1]")
        if self.a <= 0.0 or self.a >= 1.0:
            raise ValueError(f"a={self.a} not in (0, 1)")
        total = float(self.b) + float(self.d) + float(self.u)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"b + d + u = {total}, expected 1.0")

    def to_payload(self) -> dict[str, Any]:
        return {
            "b": self.b,
            "d": self.d,
            "u": self.u,
            "a": self.a,
            "provenance": self.provenance.to_payload(),
        }


class ResolutionDocument(DocumentStruct):
    method: str
    embedding_distance: float | int | None = None
    embedding_model: str | None = None
    model: str | None = None
    pass_number: int | None = None
    confidence: float | int | None = None
    opinion: OpinionDocument | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"method": self.method}
        if self.embedding_distance is not None:
            payload["embedding_distance"] = self.embedding_distance
        if self.embedding_model is not None:
            payload["embedding_model"] = self.embedding_model
        if self.model is not None:
            payload["model"] = self.model
        if self.pass_number is not None:
            payload["pass_number"] = self.pass_number
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.opinion is not None:
            payload["opinion"] = self.opinion.to_payload()
        return payload


class StanceDocument(DocumentStruct):
    type: StanceType
    target: str
    conditions_differ: str | None = None
    note: str | None = None
    resolution: ResolutionDocument | None = None
    strength: str | None = None
    target_justification_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type.value,
            "target": self.target,
        }
        if self.conditions_differ is not None:
            payload["conditions_differ"] = self.conditions_differ
        if self.note is not None:
            payload["note"] = self.note
        if self.resolution is not None:
            payload["resolution"] = self.resolution.to_payload()
        if self.strength is not None:
            payload["strength"] = self.strength
        if self.target_justification_id is not None:
            payload["target_justification_id"] = self.target_justification_id
        return payload


class AtomicPropositionDocument(DocumentStruct, tag="atomic", tag_field="kind"):
    type: ClaimType
    body: str | None = None
    concepts: tuple[str, ...] = ()
    conditions: tuple[CelExpr, ...] = ()
    confidence: float | int | None = None
    equations: tuple[str, ...] = ()
    expression: str | None = None
    fit: FitStatisticsDocument | None = None
    listener_population: str | None = None
    lower_bound: float | int | None = None
    measure: str | None = None
    methodology: str | None = None
    name: str | None = None
    notes: str | None = None
    output_concept: str | None = None
    parameters: tuple[ParameterBindingDocument, ...] = ()
    sample_size: int | None = None
    stage: AlgorithmStage | None = None
    statement: str | None = None
    sympy: str | None = None
    target_concept: str | None = None
    uncertainty: float | int | None = None
    uncertainty_type: str | None = None
    unit: str | None = None
    upper_bound: float | int | None = None
    value: float | int | None = None
    variables: tuple[VariableBindingDocument, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": "atomic", "type": self.type.value}
        if self.body is not None:
            payload["body"] = self.body
        if self.concepts:
            payload["concepts"] = list(self.concepts)
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.confidence is not None:
            payload["confidence"] = self.confidence
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
        if self.output_concept is not None:
            payload["output_concept"] = self.output_concept
        if self.parameters:
            payload["parameters"] = [
                parameter.to_payload()
                for parameter in self.parameters
            ]
        if self.sample_size is not None:
            payload["sample_size"] = self.sample_size
        if self.stage is not None:
            payload["stage"] = str(self.stage)
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
        return payload


class IstPropositionDocument(DocumentStruct, tag="ist", tag_field="kind"):
    context: ContextReferenceDocument
    proposition: AtomicPropositionDocument | IstPropositionDocument

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": "ist",
            "context": self.context.to_payload(),
            "proposition": self.proposition.to_payload(),
        }


class ClaimDocument(DocumentStruct):
    context: ContextReferenceDocument
    proposition: AtomicPropositionDocument | IstPropositionDocument | None = None
    artifact_id: str | None = None
    artifact_code: str | None = None
    logical_ids: tuple[ClaimLogicalIdDocument, ...] = ()
    version_id: str | None = None
    type: ClaimType | None = None
    provenance: ProvenanceDocument | None = None
    id: str | None = None
    body: str | None = None
    concepts: tuple[str, ...] = ()
    conditions: tuple[CelExpr, ...] = ()
    confidence: float | int | None = None
    equations: tuple[str, ...] = ()
    expression: str | None = None
    fit: FitStatisticsDocument | None = None
    listener_population: str | None = None
    lower_bound: float | int | None = None
    measure: str | None = None
    methodology: str | None = None
    name: str | None = None
    notes: str | None = None
    output_concept: str | None = None
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

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.artifact_id is not None:
            payload["artifact_id"] = self.artifact_id
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
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
        if self.concepts:
            payload["concepts"] = list(self.concepts)
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        payload["context"] = self.context.to_payload()
        if self.proposition is not None:
            payload["proposition"] = self.proposition.to_payload()
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
        if self.output_concept is not None:
            payload["output_concept"] = self.output_concept
        if self.parameters:
            payload["parameters"] = [
                parameter.to_payload()
                for parameter in self.parameters
            ]
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
        return payload


class ClaimsFileDocument(DocumentStruct):
    source: ClaimSourceDocument
    claims: tuple[ClaimDocument, ...]
    stage: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source.to_payload(),
            "claims": [claim.to_payload() for claim in self.claims],
        }
        if self.stage is not None:
            payload["stage"] = self.stage
        return payload

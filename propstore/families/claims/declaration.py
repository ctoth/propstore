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
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import TYPE_CHECKING, Any, ClassVar, cast

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import (
    CharterField,
    CharterFtsIndex,
    CharterIndex,
    CharterRelationship,
    CharterVectorCache,
    FamilyCharter,
    FamilyModel,
)
from quire.documents import DocumentBatchSpec, document_to_payload
from quire.families import FamilyDefinition
from quire.references import FamilyReferenceIndex, ForeignKeySpec, ReferenceKey
from quire.sqlalchemy_store import DerivedSession
from quire.versions import VersionId
from sqlalchemy import delete, select
from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.families.claims.types import ClaimType
from propstore.core.conditions import (
    CheckedConditionSet,
    checked_condition_set_from_json,
    checked_condition_set_to_json,
)
from propstore.core.diagnostics import QuarantineDiagnostic
from propstore.core.relations import ClaimConceptLinkRole
from propstore.dimensions import DimensionalForm, normalize_to_si
from propstore.families.contexts.declaration import ContextReferenceDocument
from propstore.families.claims.sympy_generation import derive_equation_sympy
from propstore.provenance import Provenance
from propstore.stances import StanceType

if TYPE_CHECKING:
    import msgspec

    from propstore.compiler.ir import ClaimCompilationBundle
    from propstore.families.claims.references import ClaimReferenceRecord
    from propstore.families.claims.stages import (
        ClaimAlgorithmVariable,
    )


_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)
Justification: Any = import_module("propstore.core.justifications").Justification


def _require_claim_type(value: object) -> ClaimType:
    if not isinstance(value, str):
        raise KeyError('claim_type')
    return ClaimType(value)


CLAIM_TYPE_CONTRACT_VERSION = VersionId("2026.05.25")
AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


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
            "concept_links": tuple(link.contract_body() for link in self.concept_links),
            "value_group": (
                None if self.value_group is None else self.value_group.contract_body()
            ),
            "unit_policy": (
                None if self.unit_policy is None else self.unit_policy.contract_body()
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


class ClaimLogicalIdDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    namespace: str
    value: str
    confidence: float | int | None = None
    pass_number: int | None = None


class ClaimSourceDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    paper: str
    extraction_date: str | None = None
    extraction_model: str | None = None
    extraction_prompt_hash: str | None = None


class ProvenanceDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    page: int
    paper: str | None = None
    branch_origin: str | None = None
    date: str | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None


class FitStatisticsDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    r: float | int | None = None
    r_sd: float | int | None = None
    slope: float | int | None = None
    slope_sd: float | int | None = None


class VariableBindingDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    concept: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None


class ParameterBindingDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    name: str
    concept: str
    note: str | None = None


class OpinionDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
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


class ResolutionDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    method: str
    embedding_distance: float | int | None = None
    embedding_model: str | None = None
    model: str | None = None
    pass_number: int | None = None
    confidence: float | int | None = None
    opinion: OpinionDocument | None = None


class StanceDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    type: StanceType
    target: str
    conditions_differ: str | None = None
    note: str | None = None
    resolution: ResolutionDocument | None = None
    strength: str | None = None
    target_justification_id: str | None = None


class AtomicPropositionDocument(
    msgspec.Struct,
    tag="atomic",
    tag_field="kind",
    kw_only=True,
    forbid_unknown_fields=True,
):
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


class IstPropositionDocument(
    msgspec.Struct,
    tag="ist",
    tag_field="kind",
    kw_only=True,
    forbid_unknown_fields=True,
):
    context: ContextReferenceDocument
    proposition: AtomicPropositionDocument | IstPropositionDocument


def claim_logical_id_formatted(logical_id: ClaimLogicalIdDocument) -> str:
    return f"{logical_id.namespace}:{logical_id.value}"


def claim_primary_logical_id(claim: object) -> str | None:
    logical_ids = getattr(claim, "logical_ids", ())
    if not logical_ids:
        return None
    return claim_logical_id_formatted(logical_ids[0])


def variable_binding_name(variable: VariableBindingDocument) -> str | None:
    if variable.name is not None:
        return variable.name
    return variable.symbol


def _claim_payload_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        payload: dict[str, object] = {}
        for key, item in value.items():
            encoded = _claim_payload_value(item)
            if encoded is None or encoded == []:
                continue
            payload[str(key)] = encoded
        return payload
    if isinstance(value, tuple | list):
        return [
            _claim_payload_value(item)
            for item in value
        ]
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload) and not isinstance(value, msgspec.Struct):
        return _claim_payload_value(to_payload())
    return value


def _claim_struct_payload(document: msgspec.Struct) -> dict[str, Any]:
    payload = _claim_payload_value(msgspec.to_builtins(document))
    if not isinstance(payload, dict):
        raise TypeError("claim document payload must be a mapping")
    return cast(dict[str, Any], payload)


def claim_document_to_payload(document: ClaimDocument) -> dict[str, Any]:
    return _claim_struct_payload(document)


class AuthoredClaim(FamilyModel):
    pass


def _validate_claim_type_contract(document: msgspec.Struct) -> None:
    claim_type = getattr(document, "type")
    if claim_type is None:
        return
    claim_type_contract_for(claim_type)


AUTHORED_CLAIM_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="authored_claim",
        name="authored_claim",
        contract_version=AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-authored_claim",
            contract_version=AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION,
            doc_type=AuthoredClaim,
            placement=FlatYamlPlacement(".derived/authored_claim", str),
        ),
        identity_field="id",
        reference_keys=(
            ReferenceKey.field("artifact_id"),
            ReferenceKey.field("logical_ids[].value"),
            ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
        ),
    ),
    model=AuthoredClaim,
    fields=(
        CharterField(
            "id",
            str | None,
            primary_key=True,
            nullable=True,
            document_name="artifact_id",
            document_order=3,
        ),
        CharterField(
            "context",
            ContextReferenceDocument,
            parse_boundary="json",
            nullable=False,
            document_order=0,
            foreign_key=ForeignKeySpec(
                name="claim_context",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="context.id",
                target_family="contexts",
            ),
        ),
        CharterField(
            "proposition",
            AtomicPropositionDocument | IstPropositionDocument,
            parse_boundary="json",
            nullable=True,
            document_order=1,
        ),
        CharterField(
            "source",
            ClaimSourceDocument,
            parse_boundary="json",
            nullable=True,
            document_order=2,
        ),
        CharterField("artifact_code", str, artifact=True, nullable=True),
        CharterField(
            "logical_ids",
            tuple[ClaimLogicalIdDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("version_id", str, nullable=True),
        CharterField("type", ClaimType, nullable=True),
        CharterField(
            "provenance",
            ProvenanceDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField("source_local_id", str, document_name="id", nullable=True),
        CharterField("body", str, nullable=True),
        CharterField(
            "concepts",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            foreign_key=ForeignKeySpec(
                name="claim_concepts",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="concepts[]",
                target_family="concepts",
                many=True,
                required=False,
            ),
        ),
        CharterField(
            "conditions",
            tuple[CelExpr, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("confidence", float | int | None, nullable=True),
        CharterField(
            "equations",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("expression", str, nullable=True),
        CharterField(
            "fit",
            FitStatisticsDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField("listener_population", str, nullable=True),
        CharterField("lower_bound", float | int | None, nullable=True),
        CharterField("measure", str, nullable=True),
        CharterField("methodology", str, nullable=True),
        CharterField("name", str, nullable=True),
        CharterField("notes", str, nullable=True),
        CharterField(
            "output_concept",
            str,
            nullable=True,
            foreign_key=ForeignKeySpec(
                name="claim_output_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="output_concept",
                target_family="concepts",
                required=False,
            ),
        ),
        CharterField(
            "parameters",
            tuple[ParameterBindingDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            foreign_key=ForeignKeySpec(
                name="claim_parameter_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="parameters[].concept",
                target_family="concepts",
                required=False,
            ),
        ),
        CharterField("sample_size", int, nullable=True),
        CharterField("stage", AlgorithmStage | None, nullable=True),
        CharterField(
            "stances",
            tuple[StanceDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            foreign_key=ForeignKeySpec(
                name="claim_stance_target",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="stances[].target",
                target_family="claims",
                required=False,
            ),
        ),
        CharterField("statement", str, nullable=True),
        CharterField("sympy", str, nullable=True),
        CharterField(
            "target_concept",
            str,
            nullable=True,
            foreign_key=ForeignKeySpec(
                name="claim_measurement_target_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="target_concept",
                target_family="concepts",
                required=False,
            ),
        ),
        CharterField("uncertainty", float | int | None, nullable=True),
        CharterField("uncertainty_type", str, nullable=True),
        CharterField("unit", str, nullable=True),
        CharterField("upper_bound", float | int | None, nullable=True),
        CharterField("value", float | int | None, nullable=True),
        CharterField(
            "variables",
            tuple[VariableBindingDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
            foreign_key=ForeignKeySpec(
                name="claim_variable_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claims",
                source_field="variables[].concept",
                target_family="concepts",
                required=False,
            ),
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
    validators=(_validate_claim_type_contract,),
)


if TYPE_CHECKING:

    class ClaimDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
        context: ContextReferenceDocument
        proposition: AtomicPropositionDocument | IstPropositionDocument | None = None
        source: ClaimSourceDocument | None = None
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
        def primary_logical_id(self) -> str | None: ...

        def to_payload(self) -> dict[str, Any]: ...

else:
    ClaimDocument: Any = AUTHORED_CLAIM_CHARTER.generated_document()
    ClaimDocument.__name__ = "ClaimDocument"
    ClaimDocument.__qualname__ = "ClaimDocument"
    ClaimDocument.__module__ = __name__
    ClaimDocument.primary_logical_id = property(claim_primary_logical_id)
    ClaimDocument.to_payload = claim_document_to_payload

    def _claim_bound_payload(document: msgspec.Struct) -> dict[str, Any]:
        return _claim_struct_payload(document)

    for _claim_payload_type in (
        ClaimLogicalIdDocument,
        ClaimSourceDocument,
        ProvenanceDocument,
        FitStatisticsDocument,
        VariableBindingDocument,
        ParameterBindingDocument,
        OpinionDocument,
        ResolutionDocument,
        StanceDocument,
        AtomicPropositionDocument,
        IstPropositionDocument,
    ):
        _claim_payload_type.to_payload = _claim_bound_payload
    del _claim_payload_type
    ClaimLogicalIdDocument.formatted = property(claim_logical_id_formatted)
    VariableBindingDocument.binding_name = property(variable_binding_name)


class Claim(FamilyModel):
    def concept_ids_for_role(self, role: ClaimConceptLinkRole) -> tuple[str, ...]:
        return tuple(
            str(link.concept_id)
            for link in self.concept_links
            if link.role is role
        )

    @property
    def logical_ids(self) -> tuple[Mapping[str, object], ...]:
        if not self.logical_ids_json:
            return ()
        loaded = json.loads(self.logical_ids_json)
        if not isinstance(loaded, list):
            raise ValueError("claim logical_ids_json must decode to a list")
        entries: list[Mapping[str, object]] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                raise ValueError("claim logical_ids_json entries must be mappings")
            entries.append(entry)
        return tuple(entries)

    @property
    def output_concept_id(self) -> str | None:
        concept_ids = self.concept_ids_for_role(ClaimConceptLinkRole.OUTPUT)
        return concept_ids[0] if concept_ids else None

    @property
    def value_concept_id(self) -> str | None:
        return self.output_concept_id or self.target_concept

    @property
    def about_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.ABOUT)

    @property
    def input_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.INPUT)

    @property
    def target_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.TARGET)

    @property
    def checked_conditions(self) -> CheckedConditionSet | None:
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_ir:
            return None
        loaded = json.loads(text_payload.conditions_ir)
        if not isinstance(loaded, Mapping):
            raise ValueError("claim conditions_ir must decode to a mapping")
        return checked_condition_set_from_json(loaded)

    @property
    def conditions(self) -> tuple[CelExpr, ...]:
        checked_conditions = self.checked_conditions
        if checked_conditions is not None:
            return to_cel_exprs(checked_conditions.sources)
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_cel:
            return ()
        loaded = json.loads(text_payload.conditions_cel)
        if not isinstance(loaded, list):
            raise ValueError("claim conditions_cel must decode to a list")
        return to_cel_exprs(str(item) for item in loaded)

    @property
    def variables(self) -> tuple[ClaimAlgorithmVariable, ...]:
        from propstore.families.claims.stages import parse_claim_algorithm_variables

        algorithm_payload = self.algorithm_payload
        if algorithm_payload is None:
            return ()
        return parse_claim_algorithm_variables(algorithm_payload.variables_json)

    def variable_bindings(self) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for variable in self.variables:
            if variable.concept_id is None:
                continue
            name = variable.name or variable.symbol
            if name:
                bindings[name] = str(variable.concept_id)
        return bindings

    def variable_concept_ids(self) -> tuple[str, ...]:
        return tuple(
            str(variable.concept_id)
            for variable in self.variables
            if variable.concept_id is not None
        )

    def variable_payload(self) -> list[dict[str, Any]] | None:
        from propstore.families.claims.stages import claim_algorithm_variable_payload

        if not self.variables:
            return None
        return [claim_algorithm_variable_payload(variable) for variable in self.variables]

    def to_source_claim_payload(self) -> dict[str, Any]:
        numeric_payload = self.numeric_payload
        text_payload = self.text_payload
        algorithm_payload = self.algorithm_payload
        source: dict[str, Any] = {
            "id": self.id,
            "type": self.type.value,
            "target_concept": self.target_concept,
            "context": {"id": self.context_id},
            "source_paper": self.source_paper,
            "provenance": json.loads(self.provenance_json)
            if self.provenance_json
            else None,
        }
        if self.type is ClaimType.PARAMETER and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if (
            self.type is ClaimType.MEASUREMENT
            and self.output_concept_id is not None
            and self.target_concept is None
        ):
            source["target_concept"] = self.output_concept_id
        if self.type is ClaimType.ALGORITHM and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if numeric_payload is not None:
            source.update(
                value=numeric_payload.value,
                lower_bound=numeric_payload.lower_bound,
                upper_bound=numeric_payload.upper_bound,
                uncertainty=numeric_payload.uncertainty,
                uncertainty_type=numeric_payload.uncertainty_type,
                sample_size=numeric_payload.sample_size,
                unit=numeric_payload.unit,
            )
        if text_payload is not None:
            source.update(
                conditions=json.loads(text_payload.conditions_cel)
                if text_payload.conditions_cel
                else [],
                statement=text_payload.statement,
                expression=text_payload.expression,
                sympy=text_payload.sympy_generated,
                name=text_payload.name,
                measure=text_payload.measure,
                listener_population=text_payload.listener_population,
                methodology=text_payload.methodology,
                notes=text_payload.notes,
            )
        if algorithm_payload is not None:
            source.update(
                body=algorithm_payload.body,
                stage=algorithm_payload.algorithm_stage,
            )
            variable_payload = self.variable_payload()
            if variable_payload is not None:
                source["variables"] = variable_payload
        return {key: value for key, value in source.items() if value is not None}


class ClaimConceptLink(FamilyModel):
    pass


class ClaimNumericPayload(FamilyModel):
    pass


class ClaimTextPayload(FamilyModel):
    pass


class ClaimAlgorithmPayload(FamilyModel):
    pass


class ClaimSourceAssertion(FamilyModel):
    pass


_CLAIM_FTS_SOURCE_QUERY = """
    SELECT
        c.id AS claim_id,
        COALESCE(t.statement, '') AS statement,
        COALESCE((SELECT group_concat(value, ' ') FROM json_each(t.conditions_cel)), '') AS conditions,
        COALESCE(t.expression, '') AS expression
    FROM claim_core c
    JOIN claim_text_payload t ON t.claim_id = c.id
    ORDER BY c.seq
"""


CLAIM_CORE_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="claim_core",
            name="claim_core",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-claim_core",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=Claim,
                placement=FlatYamlPlacement(".derived/claim_core", str),
            ),
            identity_field="id",
            reference_keys=(
                ReferenceKey.field("primary_logical_id"),
                ReferenceKey.field("logical_ids[].value"),
                ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
            ),
        ),
        model=Claim,
        fields=(
            CharterField("id", str, primary_key=True, nullable=False),
            CharterField("primary_logical_id", str, nullable=False, default_sql="''"),
            CharterField("logical_ids_json", str, nullable=False, default_sql="'[]'"),
            CharterField("version_id", str, nullable=False, default_sql="''"),
            CharterField("content_hash", str, nullable=False, default_sql="''"),
            CharterField("seq", int, nullable=False),
            CharterField("type", ClaimType, nullable=False),
            CharterField("target_concept", str),
            CharterField(
                "source_slug",
                str,
                foreign_key=ForeignKeySpec(
                    name="claim_source",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    source_family="claim_core",
                    source_field="source_slug",
                    target_family="source",
                    target_field="slug",
                    required=False,
                ),
            ),
            CharterField("source_paper", str, nullable=False),
            CharterField("provenance_page", int, nullable=False),
            CharterField("provenance_json", str),
            CharterField("context_id", str),
            CharterField("premise_kind", str, nullable=False, default_sql="'ordinary'"),
            CharterField("branch", str),
            CharterField("build_status", str, nullable=False, default_sql="'ingested'"),
            CharterField("stage", str),
            CharterField("promotion_status", str),
        ),
        indexes=(
            CharterIndex("idx_claim_core_target", ("target_concept",)),
            CharterIndex("idx_claim_core_type", ("type",)),
            CharterIndex("idx_claim_core_primary_logical_id", ("primary_logical_id",)),
            CharterIndex("idx_claim_core_build_status", ("build_status",)),
            CharterIndex("idx_claim_core_stage", ("stage",)),
            CharterIndex("idx_claim_core_promotion_status", ("promotion_status",)),
        ),
        fts_indexes=(
            CharterFtsIndex(
                "claim_fts",
                "claim_id",
                ("statement", "conditions", "expression"),
                source_query=_CLAIM_FTS_SOURCE_QUERY,
            ),
        ),
        vector_caches=(
            CharterVectorCache(
                "claim_embeddings",
                table="claim_vec_{model_identity_hash}_{dimensions}",
                entity_id_field="id",
                source_seq_field="seq",
                source_content_hash_field="content_hash",
                status_table="embedding_status",
            ),
        ),
        relationships=(
            CharterRelationship(
                "concept_links",
                target_family="claim_concept_link",
                foreign_key="claim_id",
                back_populates="claim",
                association_object=True,
                order_by=("ordinal",),
            ),
            CharterRelationship(
                "source",
                target_family="source",
                foreign_key="source_slug",
                uselist=False,
            ),
            CharterRelationship(
                "numeric_payload",
                target_family="claim_numeric_payload",
                foreign_key="claim_id",
                back_populates="claim",
                uselist=False,
            ),
            CharterRelationship(
                "text_payload",
                target_family="claim_text_payload",
                foreign_key="claim_id",
                back_populates="claim",
                uselist=False,
            ),
            CharterRelationship(
                "algorithm_payload",
                target_family="claim_algorithm_payload",
                foreign_key="claim_id",
                back_populates="claim",
                uselist=False,
            ),
            CharterRelationship(
                "source_assertions",
                target_family="claim_source_assertion",
                foreign_key="claim_id",
                back_populates="claim",
                association_object=True,
                order_by=("ordinal",),
            ),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )


CLAIM_CONCEPT_LINK_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="claim_concept_link",
            name="claim_concept_link",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-claim_concept_link",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=ClaimConceptLink,
                placement=FlatYamlPlacement(".derived/claim_concept_link", str),
            ),
            identity_field="claim_id",
        ),
        model=ClaimConceptLink,
        fields=(
            CharterField(
                "claim_id",
                str,
                primary_key=True,
                nullable=False,
                foreign_key=ForeignKeySpec(
                    name="claim_concept_link_claim",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    source_family="claim_concept_link",
                    source_field="claim_id",
                    target_family="claim_core",
                    target_field="id",
                    required=True,
                ),
            ),
            CharterField(
                "concept_id",
                str,
                primary_key=True,
                nullable=False,
                foreign_key=ForeignKeySpec(
                    name="claim_concept_link_concept",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    source_family="claim_concept_link",
                    source_field="concept_id",
                    target_family="concept",
                    target_field="id",
                    required=True,
                ),
            ),
            CharterField("role", ClaimConceptLinkRole, primary_key=True, nullable=False),
            CharterField("ordinal", int, primary_key=True, nullable=False),
            CharterField("binding_name", str),
        ),
        indexes=(
            CharterIndex("idx_claim_concept_link_claim", ("claim_id",)),
            CharterIndex("idx_claim_concept_link_concept", ("concept_id",)),
            CharterIndex("idx_claim_concept_link_role", ("role",)),
        ),
        relationships=(
            CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="concept_links",
                uselist=False,
            ),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )


CLAIM_PAYLOAD_CHARTERS: tuple[FamilyCharter, FamilyCharter, FamilyCharter] = (
        FamilyCharter(
            family=FamilyDefinition(
                key="claim_numeric_payload",
                name="claim_numeric_payload",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-claim_numeric_payload",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ClaimNumericPayload,
                    placement=FlatYamlPlacement(".derived/claim_numeric_payload", str),
                ),
                identity_field="claim_id",
            ),
            model=ClaimNumericPayload,
            fields=(
                CharterField(
                    "claim_id",
                    str,
                    primary_key=True,
                    nullable=False,
                    foreign_key=ForeignKeySpec(
                        name="claim_numeric_payload_claim",
                        contract_version=_WORLD_CONTRACT_VERSION,
                        source_family="claim_numeric_payload",
                        source_field="claim_id",
                        target_family="claim_core",
                        target_field="id",
                        required=True,
                    ),
                ),
                CharterField("value", float),
                CharterField("lower_bound", float),
                CharterField("upper_bound", float),
                CharterField("uncertainty", float),
                CharterField("uncertainty_type", str),
                CharterField("sample_size", int),
                CharterField("confidence", float),
                CharterField("unit", str),
                CharterField("value_si", float),
                CharterField("lower_bound_si", float),
                CharterField("upper_bound_si", float),
            ),
            relationships=(
                CharterRelationship(
                    "claim",
                    target_family="claim_core",
                    foreign_key="claim_id",
                    back_populates="numeric_payload",
                    uselist=False,
                ),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="claim_text_payload",
                name="claim_text_payload",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-claim_text_payload",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ClaimTextPayload,
                    placement=FlatYamlPlacement(".derived/claim_text_payload", str),
                ),
                identity_field="claim_id",
            ),
            model=ClaimTextPayload,
            fields=(
                CharterField(
                    "claim_id",
                    str,
                    primary_key=True,
                    nullable=False,
                    foreign_key=ForeignKeySpec(
                        name="claim_text_payload_claim",
                        contract_version=_WORLD_CONTRACT_VERSION,
                        source_family="claim_text_payload",
                        source_field="claim_id",
                        target_family="claim_core",
                        target_field="id",
                        required=True,
                    ),
                ),
                CharterField("conditions_cel", str),
                CharterField("conditions_ir", str),
                CharterField("statement", str),
                CharterField("expression", str),
                CharterField("sympy_generated", str),
                CharterField("sympy_error", str),
                CharterField("name", str),
                CharterField("measure", str),
                CharterField("listener_population", str),
                CharterField("methodology", str),
                CharterField("notes", str),
                CharterField("description", str),
                CharterField("auto_summary", str),
            ),
            relationships=(
                CharterRelationship(
                    "claim",
                    target_family="claim_core",
                    foreign_key="claim_id",
                    back_populates="text_payload",
                    uselist=False,
                ),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
        FamilyCharter(
            family=FamilyDefinition(
                key="claim_algorithm_payload",
                name="claim_algorithm_payload",
                contract_version=_WORLD_CONTRACT_VERSION,
                artifact_family=ArtifactFamily(
                    name="propstore-world-claim_algorithm_payload",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    doc_type=ClaimAlgorithmPayload,
                    placement=FlatYamlPlacement(".derived/claim_algorithm_payload", str),
                ),
                identity_field="claim_id",
            ),
            model=ClaimAlgorithmPayload,
            fields=(
                CharterField(
                    "claim_id",
                    str,
                    primary_key=True,
                    nullable=False,
                    foreign_key=ForeignKeySpec(
                        name="claim_algorithm_payload_claim",
                        contract_version=_WORLD_CONTRACT_VERSION,
                        source_family="claim_algorithm_payload",
                        source_field="claim_id",
                        target_family="claim_core",
                        target_field="id",
                        required=True,
                    ),
                ),
                CharterField("body", str),
                CharterField("canonical_ast", str),
                CharterField("variables_json", str),
                CharterField(
                    "algorithm_stage",
                    str,
                    metadata={"semantic_type": "propstore.core.algorithm_stage.AlgorithmStage"},
                ),
            ),
            indexes=(CharterIndex("idx_claim_algorithm_stage", ("algorithm_stage",)),),
            relationships=(
                CharterRelationship(
                    "claim",
                    target_family="claim_core",
                    foreign_key="claim_id",
                    back_populates="algorithm_payload",
                    uselist=False,
                ),
            ),
            semantic_metadata={"semantic": "propstore.world"},
        ),
    )


CLAIM_SOURCE_ASSERTION_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="claim_source_assertion",
            name="claim_source_assertion",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-claim_source_assertion",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=ClaimSourceAssertion,
                placement=FlatYamlPlacement(".derived/claim_source_assertion", str),
            ),
            identity_field="claim_id",
        ),
        model=ClaimSourceAssertion,
        fields=(
            CharterField(
                "claim_id",
                str,
                primary_key=True,
                nullable=False,
                foreign_key=ForeignKeySpec(
                    name="claim_source_assertion_claim",
                    contract_version=_WORLD_CONTRACT_VERSION,
                    source_family="claim_source_assertion",
                    source_field="claim_id",
                    target_family="claim_core",
                    target_field="id",
                    required=True,
                ),
            ),
            CharterField("source_assertion_id", str, nullable=False),
            CharterField("ordinal", int, primary_key=True, nullable=False),
        ),
        indexes=(
            CharterIndex("idx_claim_source_assertion_claim", ("claim_id",)),
            CharterIndex("idx_claim_source_assertion_source", ("source_assertion_id",)),
        ),
        relationships=(
            CharterRelationship(
                "claim",
                target_family="claim_core",
                foreign_key="claim_id",
                back_populates="source_assertions",
                uselist=False,
            ),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )


class JustificationProvenanceDocument(
    msgspec.Struct,
    kw_only=True,
    forbid_unknown_fields=True,
):
    paper: str | None = None
    page: int | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None


class JustificationAttackTargetDocument(
    msgspec.Struct,
    kw_only=True,
    forbid_unknown_fields=True,
):
    target_claim: str | None = None
    target_justification_id: str | None = None
    target_premise_index: int | None = None


JUSTIFICATION_CHARTER: FamilyCharter = FamilyCharter(
        family=FamilyDefinition(
            key="justification",
            name="justification",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-justification",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=Justification,
                placement=FlatYamlPlacement(".derived/justification", str),
            ),
            identity_field="id",
            reference_keys=(ReferenceKey.field("id"),),
        ),
        model=Justification,
        fields=(
            CharterField("id", str, primary_key=True, nullable=True),
            CharterField(
                "justification_kind",
                str,
                nullable=True,
                document_name="rule_kind",
            ),
            CharterField(
                "conclusion_claim_id",
                str,
                nullable=True,
                document_name="conclusion",
                foreign_key=ForeignKeySpec(
                    name="justification_conclusion",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="justifications",
                    source_field="conclusion",
                    target_family="claims",
                    required=False,
                ),
            ),
            CharterField(
                "premise_claim_ids",
                tuple[str, ...],
                parse_boundary="json",
                nullable=False,
                document_name="premises",
                default=(),
                foreign_key=ForeignKeySpec(
                    name="justification_premises",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="justifications",
                    source_field="premises[]",
                    target_family="claims",
                    many=True,
                    required=False,
                ),
            ),
            CharterField("source_relation_type", str, document=False),
            CharterField("source_claim_id", str, document=False),
            CharterField(
                "provenance_json",
                JustificationProvenanceDocument,
                parse_boundary="json",
                nullable=True,
                document_name="provenance",
            ),
            CharterField(
                "rule_strength",
                str,
                nullable=True,
                default_sql="'defeasible'",
            ),
            CharterField(
                "attack_target",
                JustificationAttackTargetDocument,
                parse_boundary="json",
                nullable=True,
            ),
            CharterField("artifact_code", str, artifact=True, nullable=True),
        ),
        semantic_metadata={"semantic": "propstore.world"},
)

if TYPE_CHECKING:

    class JustificationDocument(msgspec.Struct, forbid_unknown_fields=True):
        id: str | None = None
        rule_kind: str | None = None
        conclusion: str | None = None
        premises: tuple[str, ...] = ()
        provenance: JustificationProvenanceDocument | None = None
        rule_strength: str | None = None
        attack_target: JustificationAttackTargetDocument | None = None
        artifact_code: str | None = None

else:
    JustificationDocument: Any = JUSTIFICATION_CHARTER.generated_document()
    JustificationDocument.__module__ = __name__


def justification_document_to_payload(document: JustificationDocument) -> dict[str, Any]:
    payload = _claim_struct_payload(document)
    for key in ("provenance", "attack_target"):
        value = payload.get(key)
        if isinstance(value, str):
            loaded = json.loads(value)
            if not isinstance(loaded, dict):
                raise TypeError(f"justification {key} payload must decode to a mapping")
            payload[key] = loaded
    return payload


if not TYPE_CHECKING:
    JustificationProvenanceDocument.to_payload = _claim_bound_payload
    JustificationAttackTargetDocument.to_payload = _claim_bound_payload
    JustificationDocument.to_payload = justification_document_to_payload


from propstore.families.documents.sources import SourceClaimDocument, SourceJustificationDocument

CLAIM_BATCH_SPEC = DocumentBatchSpec(
    batch_name="claims",
    item_type=ClaimDocument,
    items_field="claims",
    inherited_item_fields=("source",),
)
SOURCE_CLAIM_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-claims",
    item_type=SourceClaimDocument,
    items_field="claims",
    inherited_item_fields=("source", "produced_by"),
)
SOURCE_JUSTIFICATION_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-justifications",
    item_type=SourceJustificationDocument,
    items_field="justifications",
    inherited_item_fields=("source", "produced_by"),
)
object.__setattr__(
    AUTHORED_CLAIM_CHARTER,
    "batch_specs",
    (CLAIM_BATCH_SPEC, SOURCE_CLAIM_BATCH_SPEC),
)
object.__setattr__(
    JUSTIFICATION_CHARTER,
    "batch_specs",
    (SOURCE_JUSTIFICATION_BATCH_SPEC,),
)


@dataclass(frozen=True)
class ClaimWriteModels:
    claims: tuple[Claim, ...]
    numeric_payloads: tuple[ClaimNumericPayload, ...]
    text_payloads: tuple[ClaimTextPayload, ...]
    algorithm_payloads: tuple[ClaimAlgorithmPayload, ...]
    source_assertions: tuple[ClaimSourceAssertion, ...]
    concept_links: tuple[ClaimConceptLink, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


@dataclass(frozen=True)
class RawIdQuarantineModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[Any, ...]


@dataclass(frozen=True)
class PromotionBlockedModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[Any, ...]


@dataclass(frozen=True)
class ClaimPromotionStatusRow:
    claim_id: str
    promotion_status: str


def source_branch_promotion_status_rows(
    derived: DerivedSession,
    *,
    branch: str,
) -> tuple[ClaimPromotionStatusRow, ...]:
    claim_core = derived.schema.table(CLAIM_CORE_CHARTER.family.name)
    return tuple(
        ClaimPromotionStatusRow(
            claim_id=str(row.id),
            promotion_status=(
                "ready" if row.promotion_status is None else str(row.promotion_status)
            ),
        )
        for row in derived.session.execute(
            select(claim_core.c.id, claim_core.c.promotion_status)
            .where(claim_core.c.branch == branch)
            .order_by(claim_core.c.seq, claim_core.c.id)
        )
    )


def _numeric_si_value(
    value: object,
    *,
    unit: object,
    form_definition: DimensionalForm | None,
) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    if form_definition is None:
        return value
    if form_definition.unit_symbol is None:
        return value
    return normalize_to_si(
        float(value),
        None if unit is None else str(unit),
        form_definition,
    )


def _claim_form_definition(
    claim_doc: object,
    concept_registry: Mapping[str, Mapping[str, Any]],
    form_registry: Mapping[str, DimensionalForm] | None,
) -> DimensionalForm | None:
    if form_registry is None:
        return None
    concept_id = (
        getattr(claim_doc, "output_concept", None)
        or getattr(claim_doc, "target_concept", None)
    )
    if concept_id is None:
        return None
    concept_payload = concept_registry.get(str(concept_id))
    if not isinstance(concept_payload, Mapping):
        return None
    form_name = concept_payload.get("form")
    if not isinstance(form_name, str) or not form_name:
        return None
    return form_registry.get(form_name)


def compile_claim_models(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: Mapping[str, Mapping[str, Any]],
    *,
    form_registry: Mapping[str, DimensionalForm] | None = None,
    source_slugs: Collection[str] = (),
) -> ClaimWriteModels:
    from propstore.claims import claim_file_filename, claim_file_stage
    from propstore.description_generator import generate_description
    from propstore.families.claims.references import build_claim_file_reference_index
    from propstore.families.claims.stages import claim_algorithm_canonical_ast

    claim_seq = 0
    claim_models: list[Claim] = []
    numeric_payloads: list[ClaimNumericPayload] = []
    text_payloads: list[ClaimTextPayload] = []
    algorithm_payloads: list[ClaimAlgorithmPayload] = []
    source_assertions: list[ClaimSourceAssertion] = []
    claim_links: list[ClaimConceptLink] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    seen_claim_versions: dict[str, str] = {}
    emitted_version_conflicts: set[tuple[str, str, str]] = set()
    seen_claim_link_keys: set[tuple[str, ClaimConceptLinkRole, int, str]] = set()
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
            claim_doc = semantic_claim.resolved_claim
            provenance = claim_doc.provenance
            provenance_payload = (
                None
                if provenance is None
                else document_to_payload(provenance)
            )
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(semantic_claim.checked_conditions),
                    sort_keys=True,
                )
                if semantic_claim.checked_conditions is not None
                else None
            )
            logical_ids_payload = [
                document_to_payload(logical_id)
                for logical_id in claim_doc.logical_ids
            ]
            source_slug = (
                semantic_claim.source_paper
                if semantic_claim.source_paper in source_slugs
                else None
            )
            claim_values: dict[str, object] = {
                "id": semantic_claim.artifact_id or claim_doc.artifact_id,
                "primary_logical_id": claim_primary_logical_id(claim_doc) or "",
                "logical_ids_json": json.dumps(logical_ids_payload),
                "version_id": claim_doc.version_id or "",
                "seq": claim_seq,
                "type": claim_doc.type,
                "target_concept": claim_doc.target_concept,
                "source_slug": source_slug,
                "source_paper": (
                    semantic_claim.source_paper
                    if provenance is None or provenance.paper is None
                    else provenance.paper
                ),
                "provenance_page": 0 if provenance is None else provenance.page,
                "provenance_json": (
                    None
                    if provenance_payload is None
                    else json.dumps(provenance_payload, sort_keys=True)
                ),
                "context_id": claim_doc.context.id,
                "premise_kind": "ordinary",
                "branch": None,
                "build_status": "ingested",
                "stage": file_stage,
                "promotion_status": None,
            }
            if file_stage is not None:
                claim_values["stage"] = file_stage
            claim_id = claim_values.get("id")
            if not isinstance(claim_id, str) or not claim_id:
                raise TypeError("compiled claim id must be a non-empty string")
            version_id = claim_values.get("version_id")
            if not isinstance(version_id, str):
                raise TypeError("compiled claim version_id must be a string")
            if claim_id in seen_claim_versions:
                existing_version = seen_claim_versions[claim_id]
                if existing_version == version_id:
                    continue
                conflict_key = (claim_id, existing_version, version_id)
                if conflict_key not in emitted_version_conflicts:
                    quarantine_diagnostics.append(
                        QuarantineDiagnostic(
                            artifact_id=claim_id,
                            kind="claim",
                            diagnostic_kind="claim_version_conflict",
                            message=(
                                f"Claim logical id {claim_id!r} appears with "
                                "multiple version_id values"
                            ),
                            file=semantic_claim.filename,
                        )
                    )
                    emitted_version_conflicts.add(conflict_key)
                continue
            form_definition = _claim_form_definition(
                claim_doc,
                concept_registry,
                form_registry,
            )
            numeric_values = {
                "claim_id": claim_id,
                "value": claim_doc.value,
                "lower_bound": claim_doc.lower_bound,
                "upper_bound": claim_doc.upper_bound,
                "uncertainty": claim_doc.uncertainty,
                "uncertainty_type": claim_doc.uncertainty_type,
                "sample_size": claim_doc.sample_size,
                "confidence": claim_doc.confidence,
                "unit": claim_doc.unit,
                "value_si": _numeric_si_value(
                    claim_doc.value,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
                "lower_bound_si": _numeric_si_value(
                    claim_doc.lower_bound,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
                "upper_bound_si": _numeric_si_value(
                    claim_doc.upper_bound,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
            }
            sympy_derivation = (
                derive_equation_sympy(
                    authored_sympy=claim_doc.sympy,
                    expression=claim_doc.expression,
                )
                if claim_doc.type is ClaimType.EQUATION
                else None
            )
            text_values = {
                "claim_id": claim_id,
                "conditions_cel": (
                    json.dumps(list(claim_doc.conditions))
                    if claim_doc.conditions
                    else None
                ),
                "conditions_ir": conditions_ir,
                "statement": claim_doc.statement,
                "expression": claim_doc.expression,
                "sympy_generated": (
                    claim_doc.sympy
                    if sympy_derivation is None
                    else sympy_derivation.generated
                ),
                "sympy_error": (
                    None
                    if sympy_derivation is None
                    else sympy_derivation.error
                ),
                "name": claim_doc.name,
                "measure": claim_doc.measure,
                "listener_population": claim_doc.listener_population,
                "methodology": claim_doc.methodology,
                "notes": claim_doc.notes,
                "description": None,
                "auto_summary": generate_description(claim_doc, concept_registry),
            }
            algorithm_values = {
                "claim_id": claim_id,
                "body": claim_doc.body,
                "canonical_ast": claim_algorithm_canonical_ast(
                    claim_doc.body,
                    claim_doc.variables,
                ),
                "variables_json": (
                    json.dumps([
                        document_to_payload(variable)
                        for variable in claim_doc.variables
                    ])
                    if claim_doc.variables
                    else None
                ),
                "algorithm_stage": claim_doc.stage,
            }
            claim_model = Claim(**claim_values)
            numeric_payload = ClaimNumericPayload(**numeric_values)
            text_payload = ClaimTextPayload(**text_values)
            algorithm_payload = ClaimAlgorithmPayload(**algorithm_values)
            source_assertion = ClaimSourceAssertion(
                claim_id=claim_id,
                source_assertion_id=f"ps:assertion:{claim_id}",
                ordinal=0,
            )
            claim_model.numeric_payload = numeric_payload
            claim_model.text_payload = text_payload
            claim_model.algorithm_payload = algorithm_payload
            claim_model.concept_links = []
            claim_model.source_assertions = [source_assertion]
            numeric_payload.claim = claim_model
            text_payload.claim = claim_model
            algorithm_payload.claim = claim_model
            source_assertion.claim = claim_model
            claim_models.append(claim_model)
            numeric_payloads.append(numeric_payload)
            text_payloads.append(text_payload)
            algorithm_payloads.append(algorithm_payload)
            source_assertions.append(source_assertion)
            seen_claim_versions[claim_id] = version_id
            claim_type_contract = claim_type_contract_for(claim_doc.type)
            if claim_type_contract is not None:
                for declaration in claim_type_contract.concept_links:
                    if declaration.source == "scalar":
                        if declaration.field == "output_concept":
                            linked_concepts = (
                                ((claim_doc.output_concept, None),)
                                if claim_doc.output_concept is not None
                                else ()
                            )
                        elif declaration.field == "target_concept":
                            linked_concepts = (
                                ((claim_doc.target_concept, None),)
                                if claim_doc.target_concept is not None
                                else ()
                            )
                        else:
                            raise ValueError(
                                "unsupported scalar claim concept-link field: "
                                f"{declaration.field}"
                            )
                    elif declaration.source == "list":
                        if declaration.field != "concepts":
                            raise ValueError(
                                "unsupported list claim concept-link field: "
                                f"{declaration.field}"
                            )
                        linked_concepts = tuple(
                            (concept_id, None)
                            for concept_id in claim_doc.concepts
                        )
                    elif declaration.source == "bindings":
                        if declaration.field == "variables":
                            linked_concepts = tuple(
                                (variable.concept, variable_binding_name(variable))
                                for variable in claim_doc.variables
                            )
                        elif declaration.field == "parameters":
                            linked_concepts = tuple(
                                (parameter.concept, parameter.name)
                                for parameter in claim_doc.parameters
                            )
                        else:
                            raise ValueError(
                                "unsupported binding claim concept-link field: "
                                f"{declaration.field}"
                            )
                    else:
                        raise ValueError(
                            "unsupported claim concept-link source: "
                            f"{declaration.source}"
                        )
                    for ordinal, (concept_id, binding_name) in enumerate(linked_concepts):
                        link_key = (claim_id, declaration.role, ordinal, concept_id)
                        if link_key in seen_claim_link_keys:
                            continue
                        seen_claim_link_keys.add(link_key)
                        link = ClaimConceptLink(
                            claim_id=claim_id,
                            concept_id=concept_id,
                            role=declaration.role,
                            ordinal=ordinal,
                            binding_name=binding_name,
                        )
                        link.claim = claim_model
                        claim_model.concept_links.append(link)
                        claim_links.append(link)
    return ClaimWriteModels(
        claims=tuple(claim_models),
        numeric_payloads=tuple(numeric_payloads),
        text_payloads=tuple(text_payloads),
        algorithm_payloads=tuple(algorithm_payloads),
        source_assertions=tuple(source_assertions),
        concept_links=tuple(claim_links),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_authored_justification_models(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[Any, ...]:
    models, diagnostics = compile_authored_justification_models_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return models


def compile_authored_justification_models_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Any, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    models: list[Any] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification_document_to_payload(justification)
        if not isinstance(justification_payload, dict):
            raise TypeError("justification document payload must be a mapping")
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

        models.append(
            Justification(
                id=justification_id,
                justification_kind=str(justification.rule_kind or "reported_claim"),
                conclusion_claim_id=conclusion,
                premise_claim_ids=tuple(resolved_premises),
                source_relation_type=None,
                source_claim_id=None,
                provenance_json=provenance if isinstance(provenance, dict) else None,
                rule_strength=str(justification.rule_strength or "defeasible"),
                attack_target=attack_target if isinstance(attack_target, dict) else None,
                artifact_code=justification.artifact_code,
            )
        )
    return tuple(models), tuple(diagnostics)


def compile_raw_id_quarantine_models(
    records: Sequence[Any],
) -> RawIdQuarantineModels:
    BuildDiagnostic = import_module(
        "propstore.families.diagnostics.declaration"
    ).BuildDiagnostic

    diagnostics: list[Any] = []

    for record in records:
        diagnostics.append(
            BuildDiagnostic(
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

    return RawIdQuarantineModels(
        claims=(),
        diagnostics=tuple(diagnostics),
    )


def compile_promotion_blocked_models(
    facts: Sequence[Any],
) -> PromotionBlockedModels:
    compile_promotion_blocked_diagnostics = import_module(
        "propstore.families.diagnostics.declaration"
    ).compile_promotion_blocked_diagnostics

    claims = tuple(
        Claim(
            id=fact.artifact_id,
            type=fact.claim_type,
            source_paper=fact.source_paper,
            provenance_page=0,
            primary_logical_id=fact.raw_id,
            logical_ids_json="[]",
            version_id="",
            seq=seq,
            branch=fact.source_branch,
            build_status="blocked",
            stage="source.promotion",
            promotion_status="blocked",
        )
        for seq, fact in enumerate(facts)
    )
    return PromotionBlockedModels(
        claims=claims,
        diagnostics=compile_promotion_blocked_diagnostics(facts),
    )


def write_promotion_blocked_models(
    derived: DerivedSession,
    rows: PromotionBlockedModels,
) -> None:
    delete_promotion_blocked_diagnostics = import_module(
        "propstore.families.diagnostics.declaration"
    ).delete_promotion_blocked_diagnostics

    claim_objects_by_id = {
        str(getattr(row, "id")): row
        for row in rows.claims
    }
    diagnostic_objects = tuple(rows.diagnostics)
    if claim_objects_by_id:
        claim_core = derived.schema.table(CLAIM_CORE_CHARTER.family.name)
        existing_rows = derived.session.execute(
            select(claim_core.c.id, claim_core.c.promotion_status).where(
                claim_core.c.id.in_(tuple(claim_objects_by_id))
            )
        ).all()
        preserved_claim_ids = {
            str(row.id)
            for row in existing_rows
            if row.promotion_status != "blocked"
        }
        for claim_id in preserved_claim_ids:
            claim_objects_by_id.pop(claim_id, None)
    claim_objects = tuple(claim_objects_by_id.values())
    if not claim_objects and not diagnostic_objects:
        return
    claim_ids = tuple(str(getattr(row, "id")) for row in claim_objects)
    diagnostic_claim_ids = tuple(
        sorted(
            {
                str(claim_id)
                for row in diagnostic_objects
                if getattr(row, "diagnostic_kind", None) == "promotion_blocked"
                for claim_id in (getattr(row, "claim_id", None),)
                if claim_id
            }
        )
    )
    if claim_ids:
        derived.flush()
        _delete_claim_children(derived, claim_ids)
    for claim_id in sorted(set(claim_ids) | set(diagnostic_claim_ids)):
        delete_promotion_blocked_diagnostics(derived, claim_id)
    derived.add_all(claim_objects)
    derived.add_all(diagnostic_objects)


def _delete_claim_children(
    derived: DerivedSession,
    claim_ids: tuple[str, ...],
) -> None:
    schema = derived.schema
    session = derived.session
    for table_name in (
        "claim_concept_link",
        "claim_numeric_payload",
        "claim_text_payload",
        "claim_algorithm_payload",
        "micropublication_claim",
    ):
        table = schema.tables.get(table_name)
        if table is None or "claim_id" not in table.c:
            continue
        session.execute(delete(table).where(table.c.claim_id.in_(claim_ids)))
    claim_core = schema.table("claim_core")
    session.execute(delete(claim_core).where(claim_core.c.id.in_(claim_ids)))

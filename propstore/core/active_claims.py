"""Typed runtime claim objects for active world reasoning."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core.algorithm_stage import AlgorithmStage, coerce_algorithm_stage
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.core.conditions import CheckedConditionSet, checked_condition_set_from_json
from propstore.core.claim_values import ClaimProvenance, ClaimSource
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
    ContextId,
    LogicalId,
    to_claim_id,
    to_concept_id,
)
from propstore.core.relations import ClaimConceptLinkRole, coerce_claim_concept_link_role


@dataclass(frozen=True)
class ActiveClaimVariable:
    name: str | None = None
    symbol: str | None = None
    concept_id: ConceptId | None = None
    role: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", dict(self.attributes))
        if self.concept_id is not None:
            object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))

    def to_payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.symbol is not None:
            data["symbol"] = self.symbol
        if self.concept_id is not None:
            data["concept"] = self.concept_id
        if self.role is not None:
            data["role"] = self.role
        data.update(self.attributes)
        return data


def _parse_conditions(raw: object) -> tuple[CelExpr, ...]:
    if raw is None or raw == "":
        return ()
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return to_cel_exprs((raw,))
        if isinstance(loaded, list):
            return to_cel_exprs(str(item) for item in loaded)
        return to_cel_exprs((str(loaded),))
    if isinstance(raw, (list, tuple)):
        return to_cel_exprs(str(item) for item in raw)
    return to_cel_exprs((str(raw),))


def _parse_variables(
    raw: object,
) -> tuple[ActiveClaimVariable, ...]:
    if raw is None or raw == "":
        return ()
    loaded = raw
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return ()
    if isinstance(loaded, Mapping):
        raise ValueError("algorithm claim variables must be a list of variable bindings")
    if isinstance(loaded, list):
        variables: list[ActiveClaimVariable] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                continue
            concept = entry.get("concept")
            variables.append(
                ActiveClaimVariable(
                    name=(None if entry.get("name") is None else str(entry.get("name"))),
                    symbol=(None if entry.get("symbol") is None else str(entry.get("symbol"))),
                    concept_id=(None if concept is None else to_concept_id(concept)),
                    role=(None if entry.get("role") is None else str(entry.get("role"))),
                    attributes={
                        str(key): value
                        for key, value in entry.items()
                        if key not in {"name", "symbol", "concept", "role"} and value is not None
                    },
                )
            )
        return tuple(variables)
    return ()


def _parse_checked_conditions(raw: object) -> CheckedConditionSet | None:
    if raw is None or raw == "":
        return None
    if not isinstance(raw, str):
        raise ValueError("checked claim conditions must be encoded as JSON text")
    loaded = json.loads(raw)
    if not isinstance(loaded, Mapping):
        raise ValueError("checked claim conditions must decode to a mapping")
    return checked_condition_set_from_json(loaded)


def _require_claim_concept_link_role(value: object) -> ClaimConceptLinkRole:
    role = coerce_claim_concept_link_role(value)
    if role is None:
        raise KeyError("role")
    return role


def _coerce_claim_concept_link(link: object) -> SimpleNamespace:
    return SimpleNamespace(
        claim_id=to_claim_id(getattr(link, "claim_id")),
        concept_id=to_concept_id(getattr(link, "concept_id")),
        role=_require_claim_concept_link_role(getattr(link, "role")),
        ordinal=int(getattr(link, "ordinal", 0)),
        binding_name=getattr(link, "binding_name", None),
    )


@dataclass(frozen=True)
class ActiveClaim:
    claim_id: ClaimId
    artifact_id: str
    claim_type: ClaimType | None = None
    concept_links: tuple[SimpleNamespace, ...] = field(default_factory=tuple)
    target_concept: ConceptId | None = None
    logical_ids: tuple[LogicalId, ...] = field(default_factory=tuple)
    version_id: str | None = None
    seq: int | None = None
    value: Any = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    unit: str | None = None
    conditions_cel: str | None = None
    conditions_ir: str | None = None
    statement: str | None = None
    expression: str | None = None
    sympy_generated: str | None = None
    sympy_error: str | None = None
    name: str | None = None
    measure: str | None = None
    listener_population: str | None = None
    methodology: str | None = None
    notes: str | None = None
    description: str | None = None
    auto_summary: str | None = None
    body: str | None = None
    canonical_ast: str | None = None
    variables_json: str | None = None
    algorithm_stage: AlgorithmStage | None = None
    source: ClaimSource | None = None
    provenance: ClaimProvenance | None = None
    value_si: float | None = None
    lower_bound_si: float | None = None
    upper_bound_si: float | None = None
    context_id: ContextId | None = None
    premise_kind: str | None = None
    content_hash: str | None = None
    branch: str | None = None
    build_status: str | None = None
    stage: str | None = None
    promotion_status: str | None = None
    confidence: float | None = None
    claim_probability: float | None = None
    effective_sample_size: int | None = None
    opinion_belief: float | None = None
    opinion_disbelief: float | None = None
    opinion_uncertainty: float | None = None
    opinion_base_rate: float | None = None
    source_assertion_ids: Any = None
    concept_id: ConceptId | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    conditions: tuple[CelExpr, ...] = field(default_factory=tuple)
    checked_conditions: CheckedConditionSet | None = None
    variables: tuple[ActiveClaimVariable, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_id", to_claim_id(self.claim_id))
        object.__setattr__(self, "attributes", dict(self.attributes))
        object.__setattr__(
            self,
            "concept_links",
            tuple(_coerce_claim_concept_link(link) for link in self.concept_links),
        )
        if self.claim_type is not None:
            object.__setattr__(self, "claim_type", coerce_claim_type(self.claim_type))
        if self.target_concept is not None:
            object.__setattr__(self, "target_concept", to_concept_id(self.target_concept))
        if self.algorithm_stage is not None:
            object.__setattr__(
                self,
                "algorithm_stage",
                coerce_algorithm_stage(self.algorithm_stage),
            )
        checked_conditions = self.checked_conditions
        if checked_conditions is None:
            checked_conditions = _parse_checked_conditions(self.conditions_ir)
        if self.conditions_cel and checked_conditions is None:
            raise ValueError(
                "conditional claim row is missing conditions_ir; rebuild the sidecar"
            )
        conditions = self.conditions
        if not conditions:
            if checked_conditions is not None:
                conditions = to_cel_exprs(checked_conditions.sources)
            else:
                conditions = _parse_conditions(self.conditions_cel)
        variables = self.variables or _parse_variables(self.variables_json)
        object.__setattr__(self, "checked_conditions", checked_conditions)
        object.__setattr__(self, "conditions", to_cel_exprs(conditions))
        object.__setattr__(self, "variables", tuple(variables))

    @classmethod
    def from_claim(cls, claim: ActiveClaimInput) -> ActiveClaim:
        return coerce_active_claim(claim)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ActiveClaim:
        from propstore.families.claims.projection_model import CLAIM_ROW_MODEL

        return CLAIM_ROW_MODEL.coerce(data)

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    @property
    def primary_logical_value(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].value

    @property
    def source_paper(self) -> str | None:
        return None if self.provenance is None else self.provenance.paper

    @property
    def provenance_page(self) -> int | None:
        return None if self.provenance is None else self.provenance.page

    @property
    def source_slug(self) -> str | None:
        return None if self.source is None else self.source.slug

    def concept_ids_for_role(self, role: ClaimConceptLinkRole) -> tuple[ConceptId, ...]:
        return tuple(
            link.concept_id
            for link in self.concept_links
            if link.role is role
        )

    @property
    def output_concept_id(self) -> ConceptId | None:
        concept_ids = self.concept_ids_for_role(ClaimConceptLinkRole.OUTPUT)
        return concept_ids[0] if concept_ids else None

    @property
    def value_concept_id(self) -> ConceptId | None:
        return self.output_concept_id or self.target_concept

    @property
    def about_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.ABOUT)

    @property
    def input_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.INPUT)

    @property
    def target_concept_ids(self) -> tuple[ConceptId, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.TARGET)

    def attribute_mapping(self) -> dict[str, Any]:
        data = dict(self.attributes)
        for key in (
            "content_hash",
            "branch",
            "build_status",
            "stage",
            "promotion_status",
            "confidence",
            "claim_probability",
            "effective_sample_size",
            "opinion_belief",
            "opinion_disbelief",
            "opinion_uncertainty",
            "opinion_base_rate",
            "source_assertion_ids",
            "concept_id",
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

    @property
    def display_claim_id(self) -> str:
        logical_value = self.primary_logical_value
        if logical_value:
            return logical_value
        return str(self.claim_id)

    @property
    def conditions_cel_json(self) -> str | None:
        if not self.conditions:
            return None
        return json.dumps(list(self.conditions))

    def variable_bindings(self) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for variable in self.variables:
            concept_id = None if variable.concept_id is None else str(variable.concept_id)
            if concept_id is None:
                continue
            name = variable.name or variable.symbol
            if name:
                bindings[name] = concept_id
        return bindings

    def variable_concept_ids(self) -> tuple[str, ...]:
        return tuple(
            str(variable.concept_id)
            for variable in self.variables
            if variable.concept_id is not None
        )

    def variable_payload(self) -> list[dict[str, Any]] | None:
        if not self.variables:
            return None
        return [variable.to_payload() for variable in self.variables]

    def to_dict(self) -> dict[str, Any]:
        from propstore.families.claims.projection_model import CLAIM_ROW_MODEL

        data = dict(CLAIM_ROW_MODEL.to_mapping(self))
        data["conditions"] = list(self.conditions)
        if self.branch is not None:
            data["branch"] = self.branch
        variable_payload = self.variable_payload()
        if variable_payload is not None:
            data["variables"] = variable_payload
        return data

    def to_source_claim_payload(self) -> dict[str, Any]:
        source = self.to_dict()
        if self.claim_type is ClaimType.PARAMETER and self.output_concept_id is not None:
            source["output_concept"] = str(self.output_concept_id)
        if (
            self.claim_type is ClaimType.MEASUREMENT
            and self.output_concept_id is not None
            and self.target_concept is None
        ):
            source["target_concept"] = str(self.output_concept_id)
        if self.claim_type is ClaimType.ALGORITHM and self.output_concept_id is not None:
            source["output_concept"] = str(self.output_concept_id)
        return source


ActiveClaimInput = ActiveClaim | Mapping[str, Any]


def coerce_active_claim(claim: ActiveClaimInput) -> ActiveClaim:
    if isinstance(claim, ActiveClaim):
        return claim
    return ActiveClaim.from_mapping(claim)


def coerce_active_claims(claims: Iterable[ActiveClaimInput]) -> list[ActiveClaim]:
    return [coerce_active_claim(claim) for claim in claims]

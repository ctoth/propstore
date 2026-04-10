"""Typed runtime claim objects for active world reasoning."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from propstore.core.id_types import ClaimId, ConceptId, ContextId, LogicalId, to_concept_id
from propstore.core.row_types import ClaimRow, ClaimRowInput, coerce_claim_row


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


VariableEncoding = Literal["list", "mapping"] | None


def _parse_conditions(raw: object) -> tuple[str, ...]:
    if raw is None or raw == "":
        return ()
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return (raw,)
        if isinstance(loaded, list):
            return tuple(str(item) for item in loaded)
        return (str(loaded),)
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    return (str(raw),)


def _parse_variables(
    raw: object,
) -> tuple[tuple[ActiveClaimVariable, ...], VariableEncoding]:
    if raw is None or raw == "":
        return (), None
    loaded = raw
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return (), None
    if isinstance(loaded, Mapping):
        variables = tuple(
            ActiveClaimVariable(
                name=str(name),
                concept_id=(None if concept is None else to_concept_id(concept)),
            )
            for name, concept in loaded.items()
            if isinstance(name, str) and name and isinstance(concept, str) and concept
        )
        return variables, "mapping"
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
        return tuple(variables), "list"
    return (), None


@dataclass(frozen=True)
class ActiveClaim:
    row: ClaimRow
    conditions: tuple[str, ...] = field(default_factory=tuple)
    variables: tuple[ActiveClaimVariable, ...] = field(default_factory=tuple)
    variable_encoding: VariableEncoding = None
    branch: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", tuple(str(item) for item in self.conditions))
        object.__setattr__(self, "variables", tuple(self.variables))

    @classmethod
    def from_claim_row(cls, row: ClaimRow) -> ActiveClaim:
        variables, variable_encoding = _parse_variables(row.variables_json)
        branch = row.attributes.get("branch")
        return cls(
            row=row,
            conditions=_parse_conditions(row.conditions_cel),
            variables=variables,
            variable_encoding=variable_encoding,
            branch=(None if branch is None else str(branch)),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ActiveClaim:
        return cls.from_claim_row(coerce_claim_row(data))

    def __getattr__(self, name: str) -> Any:
        return getattr(self.row, name)

    @property
    def claim_id(self) -> ClaimId:
        return self.row.claim_id

    @property
    def artifact_id(self) -> str:
        return self.row.artifact_id

    @property
    def claim_type(self) -> str | None:
        return self.row.claim_type

    @property
    def concept_id(self) -> ConceptId | None:
        return self.row.concept_id

    @property
    def target_concept(self) -> ConceptId | None:
        return self.row.target_concept

    @property
    def logical_ids(self) -> tuple[LogicalId, ...]:
        return self.row.logical_ids

    @property
    def primary_logical_id(self) -> str | None:
        return self.row.primary_logical_id

    @property
    def primary_logical_value(self) -> str | None:
        return self.row.primary_logical_value

    @property
    def source_slug(self) -> str | None:
        return self.row.source_slug

    @property
    def source_paper(self) -> str | None:
        return self.row.source_paper

    @property
    def provenance_page(self) -> int | None:
        return self.row.provenance_page

    @property
    def context_id(self) -> ContextId | None:
        return self.row.context_id

    @property
    def attributes(self) -> Mapping[str, Any]:
        return self.row.attributes

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

    def variable_payload(self) -> list[dict[str, Any]] | dict[str, str] | None:
        if not self.variables:
            return None
        if self.variable_encoding == "mapping":
            payload: dict[str, str] = {}
            for variable in self.variables:
                if variable.name is None or variable.concept_id is None:
                    continue
                payload[variable.name] = str(variable.concept_id)
            return payload
        return [variable.to_payload() for variable in self.variables]

    def to_dict(self) -> dict[str, Any]:
        data = self.row.to_dict()
        data["conditions"] = list(self.conditions)
        if self.branch is not None:
            data["branch"] = self.branch
        variable_payload = self.variable_payload()
        if variable_payload is not None:
            data["variables"] = variable_payload
        return data

    def to_source_claim_payload(self) -> dict[str, Any]:
        source = self.to_dict()
        if self.claim_type == "parameter" and self.concept_id is not None:
            source["concept"] = str(self.concept_id)
        if self.claim_type == "measurement" and self.concept_id is not None and self.target_concept is None:
            source["target_concept"] = str(self.concept_id)
        if self.claim_type == "algorithm" and self.concept_id is not None:
            source["concept"] = str(self.concept_id)
        return source


ActiveClaimInput = ActiveClaim | ClaimRow | Mapping[str, Any]


def coerce_active_claim(claim: ActiveClaimInput) -> ActiveClaim:
    if isinstance(claim, ActiveClaim):
        return claim
    if isinstance(claim, ClaimRow):
        return ActiveClaim.from_claim_row(claim)
    return ActiveClaim.from_mapping(claim)


def coerce_active_claims(claims: Iterable[ActiveClaimInput]) -> list[ActiveClaim]:
    return [coerce_active_claim(claim) for claim in claims]

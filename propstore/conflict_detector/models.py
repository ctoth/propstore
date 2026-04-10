"""Shared conflict detector models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class ConflictClaimVariable:
    concept_id: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ConflictClaimVariable | None:
        concept_id = payload.get("concept")
        if not isinstance(concept_id, str) or not concept_id:
            return None
        return cls(
            concept_id=concept_id,
            symbol=None if payload.get("symbol") is None else str(payload.get("symbol")),
            role=None if payload.get("role") is None else str(payload.get("role")),
            name=None if payload.get("name") is None else str(payload.get("name")),
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"concept": self.concept_id}
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.role is not None:
            payload["role"] = self.role
        if self.name is not None:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class ConflictClaim:
    claim_id: str
    claim_type: str | None = None
    artifact_id: str | None = None
    concept_id: str | None = None
    target_concept_id: str | None = None
    measure: str | None = None
    value: Any = None
    lower_bound: float | int | None = None
    upper_bound: float | int | None = None
    unit: str | None = None
    expression: str | None = None
    sympy: str | None = None
    body: str | None = None
    listener_population: str | None = None
    source_paper: str | None = None
    context_id: str | None = None
    conditions: tuple[str, ...] = field(default_factory=tuple)
    variables: tuple[ConflictClaimVariable, ...] = field(default_factory=tuple)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ConflictClaim | None:
        claim_id = payload.get("id") or payload.get("artifact_id")
        if not isinstance(claim_id, str) or not claim_id:
            return None
        raw_variables = payload.get("variables")
        variables = ()
        if isinstance(raw_variables, list):
            variables = tuple(
                variable
                for entry in raw_variables
                if isinstance(entry, dict)
                and (variable := ConflictClaimVariable.from_payload(entry)) is not None
            )
        raw_conditions = payload.get("conditions") or ()
        conditions = tuple(str(item) for item in raw_conditions) if isinstance(raw_conditions, list | tuple) else ()
        context_id = payload.get("context_id")
        if context_id is None:
            context_id = payload.get("context")
        return cls(
            claim_id=claim_id,
            claim_type=None if payload.get("type") is None else str(payload.get("type")),
            artifact_id=None if payload.get("artifact_id") is None else str(payload.get("artifact_id")),
            concept_id=None if payload.get("concept") is None else str(payload.get("concept")),
            target_concept_id=(
                None if payload.get("target_concept") is None else str(payload.get("target_concept"))
            ),
            measure=None if payload.get("measure") is None else str(payload.get("measure")),
            value=payload.get("value"),
            lower_bound=payload.get("lower_bound"),
            upper_bound=payload.get("upper_bound"),
            unit=None if payload.get("unit") is None else str(payload.get("unit")),
            expression=None if payload.get("expression") is None else str(payload.get("expression")),
            sympy=None if payload.get("sympy") is None else str(payload.get("sympy")),
            body=None if payload.get("body") is None else str(payload.get("body")),
            listener_population=(
                None
                if payload.get("listener_population") is None
                else str(payload.get("listener_population"))
            ),
            source_paper=None if payload.get("source_paper") is None else str(payload.get("source_paper")),
            context_id=None if context_id is None else str(context_id),
            conditions=conditions,
            variables=variables,
        )

    def with_source_condition(self) -> ConflictClaim:
        if not self.source_paper:
            return self
        source_cond = f"source == '{self.source_paper}'"
        if source_cond in self.conditions:
            return self
        return replace(self, conditions=tuple((*self.conditions, source_cond)))

    def get(self, key: str, default: object = None) -> object:
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key: str) -> object:
        if key == "id":
            return self.claim_id
        if key == "artifact_id":
            return self.artifact_id
        if key == "type":
            return self.claim_type
        if key == "concept":
            return self.concept_id
        if key == "target_concept":
            return self.target_concept_id
        if key == "measure":
            return self.measure
        if key == "value":
            return self.value
        if key == "lower_bound":
            return self.lower_bound
        if key == "upper_bound":
            return self.upper_bound
        if key == "unit":
            return self.unit
        if key == "expression":
            return self.expression
        if key == "sympy":
            return self.sympy
        if key == "body":
            return self.body
        if key == "listener_population":
            return self.listener_population
        if key == "source_paper":
            return self.source_paper
        if key == "context_id" or key == "context":
            return self.context_id
        if key == "conditions":
            return list(self.conditions)
        if key == "variables":
            return [variable.to_payload() for variable in self.variables]
        raise KeyError(key)


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[str]
    conditions_b: list[str]
    value_a: str
    value_b: str
    derivation_chain: str | None = None

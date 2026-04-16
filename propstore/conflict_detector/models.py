"""Shared conflict detector models."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, cast

from propstore.cel_types import CelExpr, to_cel_expr, to_cel_exprs


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
    conditions: tuple[CelExpr, ...] = field(default_factory=tuple)
    variables: tuple[ConflictClaimVariable, ...] = field(default_factory=tuple)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ConflictClaim | None:
        claim_id = payload.get("id") or payload.get("artifact_id")
        if not isinstance(claim_id, str) or not claim_id:
            return None
        raw_variables: object = payload.get("variables")
        variables = ()
        if isinstance(raw_variables, list):
            parsed_variables: list[ConflictClaimVariable] = []
            for raw_entry in cast(list[object], raw_variables):
                if not isinstance(raw_entry, dict):
                    continue
                variable = ConflictClaimVariable.from_payload(cast(dict[str, Any], raw_entry))
                if variable is not None:
                    parsed_variables.append(variable)
            variables = tuple(parsed_variables)
        raw_conditions: object = payload.get("conditions") or ()
        conditions: tuple[CelExpr, ...] = ()
        if isinstance(raw_conditions, list | tuple):
            conditions = to_cel_exprs(
                str(item)
                for item in cast(list[object] | tuple[object, ...], raw_conditions)
            )
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
        return replace(self, conditions=tuple((*self.conditions, to_cel_expr(source_cond))))


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    PHI_NODE = "PHI_NODE"
    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    PARAM_CONFLICT = "PARAM_CONFLICT"
    CONTEXT_PHI_NODE = "CONTEXT_PHI_NODE"


def coerce_conflict_class(value: object | None) -> ConflictClass | None:
    if value is None:
        return None
    if isinstance(value, ConflictClass):
        return value
    raw_value = str(value)
    try:
        return ConflictClass(raw_value)
    except ValueError:
        return ConflictClass(raw_value.upper())


@dataclass
class ConflictRecord:
    concept_id: str
    claim_a_id: str
    claim_b_id: str
    warning_class: ConflictClass
    conditions_a: list[CelExpr]
    conditions_b: list[CelExpr]
    value_a: str
    value_b: str
    derivation_chain: str | None = None

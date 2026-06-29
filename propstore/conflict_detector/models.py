"""Shared conflict detector models.

A :class:`ConflictClaim` is the value-typed projection of a stored claim payload
that the detectors compare. :meth:`ConflictClaim.from_payload` and
:func:`coerce_conflict_class` are validating parses of stored/serialized data
(deserialization narrowings, like the family ``_coerce_kind`` helpers), not
cross-package coercers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from condition_ir import CelExpr, to_cel_expr, to_cel_exprs


@dataclass(frozen=True)
class ConflictClaimVariable:
    concept_id: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class ConflictClaim:
    claim_id: str
    claim_type: str | None = None
    artifact_id: str | None = None
    output_concept_id: str | None = None
    target_concept_id: str | None = None
    measure: str | None = None
    value: object = None
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
    def from_payload(cls, payload: Mapping[str, Any]) -> ConflictClaim | None:
        raw_id = payload.get("id") or payload.get("artifact_id")
        if not isinstance(raw_id, str) or not raw_id:
            return None
        return cls(
            claim_id=raw_id,
            claim_type=_optional_str(payload.get("type")),
            artifact_id=_optional_str(payload.get("artifact_id")),
            output_concept_id=_optional_str(payload.get("output_concept")),
            target_concept_id=_optional_str(payload.get("target_concept")),
            measure=_optional_str(payload.get("measure")),
            value=payload.get("value"),
            lower_bound=_optional_number(payload.get("lower_bound")),
            upper_bound=_optional_number(payload.get("upper_bound")),
            unit=_optional_str(payload.get("unit")),
            expression=_optional_str(payload.get("expression")),
            sympy=_optional_str(payload.get("sympy")),
            body=_optional_str(payload.get("body")),
            listener_population=_optional_str(payload.get("listener_population")),
            source_paper=_optional_str(payload.get("source_paper")),
            context_id=_context_id_from_payload(payload),
            conditions=_conditions_from_payload(payload),
            variables=_variables_from_payload(payload),
        )

    def with_source_condition(self) -> ConflictClaim:
        if not self.source_paper:
            return self
        source_condition = to_cel_expr(f"source == '{self.source_paper}'")
        if source_condition in self.conditions:
            return self
        return replace(self, conditions=(*self.conditions, source_condition))


# --- Stored-payload deserialization boundary -------------------------------
# A stored claim payload is a genuinely untyped JSON/YAML surface. ``payload_get``
# is the single narrowing point that reads a field from a possibly-mapping value
# without committing to its element types (mirrors ``value_comparison._claim_field``);
# every value it yields is immediately narrowed to a concrete type below.


def payload_get(obj: object, key: str) -> Any:
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key)
    return None


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_number(value: object) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _context_id_from_payload(payload: Mapping[str, Any]) -> str | None:
    raw_context = payload.get("context_id")
    if raw_context is None:
        raw_context = payload.get("context")
    if isinstance(raw_context, str):
        return raw_context
    if raw_context is None:
        return None
    return _optional_str(payload_get(raw_context, "id"))


def _variables_from_payload(payload: Mapping[str, Any]) -> tuple[ConflictClaimVariable, ...]:
    variables: list[ConflictClaimVariable] = []
    for entry in payload.get("variables") or ():
        concept = payload_get(entry, "concept")
        if not isinstance(concept, str) or not concept:
            continue
        variables.append(
            ConflictClaimVariable(
                concept_id=concept,
                symbol=_optional_str(payload_get(entry, "symbol")),
                role=_optional_str(payload_get(entry, "role")),
                name=_optional_str(payload_get(entry, "name")),
            )
        )
    return tuple(variables)


def _conditions_from_payload(payload: Mapping[str, Any]) -> tuple[CelExpr, ...]:
    return to_cel_exprs(str(item) for item in (payload.get("conditions") or ()))


class ConflictClass(Enum):
    COMPATIBLE = "COMPATIBLE"
    UNKNOWN = "UNKNOWN"
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

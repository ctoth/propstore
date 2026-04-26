"""Semantic ID newtypes and coercion helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NewType

ConceptId = NewType("ConceptId", str)
ClaimId = NewType("ClaimId", str)
AssertionId = NewType("AssertionId", str)
ContextId = NewType("ContextId", str)
ConditionId = NewType("ConditionId", str)
ProvenanceGraphId = NewType("ProvenanceGraphId", str)
JustificationId = NewType("JustificationId", str)
AssumptionId = NewType("AssumptionId", str)
QueryableId = NewType("QueryableId", str)


@dataclass(frozen=True)
class LogicalId:
    namespace: str
    value: str

    @property
    def formatted(self) -> str:
        return f"{self.namespace}:{self.value}"

    def to_payload(self) -> dict[str, str]:
        return {
            "namespace": self.namespace,
            "value": self.value,
        }


def to_concept_id(value: object) -> ConceptId:
    return ConceptId(str(value))


def to_claim_id(value: object) -> ClaimId:
    return ClaimId(str(value))


def to_assertion_id(value: object) -> AssertionId:
    return AssertionId(str(value))


def to_context_id(value: object) -> ContextId:
    return ContextId(str(value))


def to_condition_id(value: object) -> ConditionId:
    return ConditionId(str(value))


def to_provenance_graph_id(value: object) -> ProvenanceGraphId:
    return ProvenanceGraphId(str(value))


def to_justification_id(value: object) -> JustificationId:
    return JustificationId(str(value))


def to_assumption_id(value: object) -> AssumptionId:
    return AssumptionId(str(value))


def to_queryable_id(value: object) -> QueryableId:
    return QueryableId(str(value))


def to_concept_ids(values: Iterable[object]) -> tuple[ConceptId, ...]:
    return tuple(to_concept_id(value) for value in values)


def to_claim_ids(values: Iterable[object]) -> tuple[ClaimId, ...]:
    return tuple(to_claim_id(value) for value in values)


def to_assumption_ids(values: Iterable[object]) -> tuple[AssumptionId, ...]:
    return tuple(to_assumption_id(value) for value in values)


def to_queryable_ids(values: Iterable[object]) -> tuple[QueryableId, ...]:
    return tuple(to_queryable_id(value) for value in values)

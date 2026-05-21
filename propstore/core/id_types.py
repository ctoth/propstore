"""Semantic ID newtypes."""

from __future__ import annotations

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

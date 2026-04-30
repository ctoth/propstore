from __future__ import annotations

from enum import StrEnum
from typing import Any

import msgspec
from quire.documents import DocumentStruct


class SameAsRelation(StrEnum):
    SAME_INDIVIDUAL = "sim:sameIndividual"
    CLAIMS_IDENTICAL = "sim:claimsIdentical"
    ALMOST_SAME_AS = "sim:almostSameAs"


class SameAsAssertionDocument(DocumentStruct):
    left_artifact_id: str
    right_artifact_id: str
    relation: SameAsRelation
    evidence_source: str
    provenance: dict[str, Any] = msgspec.field(default_factory=dict)
    confidence: float | int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "left_artifact_id": self.left_artifact_id,
            "right_artifact_id": self.right_artifact_id,
            "relation": self.relation.value,
            "evidence_source": self.evidence_source,
        }
        if self.provenance:
            payload["provenance"] = dict(self.provenance)
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


class SameAsFileDocument(DocumentStruct):
    assertions: tuple[SameAsAssertionDocument, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "assertions": [assertion.to_payload() for assertion in self.assertions]
        }

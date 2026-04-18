"""Typed document models for canonical stance YAML files."""

from __future__ import annotations

from typing import Any

from propstore.artifacts.documents.claims import ResolutionDocument
from quire.documents import DocumentStruct
from propstore.stances import StanceType


class StanceEntryDocument(DocumentStruct):
    source_claim: str | None = None
    target: str | None = None
    type: StanceType | None = None
    strength: str | None = None
    note: str | None = None
    conditions_differ: str | None = None
    resolution: ResolutionDocument | None = None
    target_justification_id: str | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.source_claim is not None:
            payload["source_claim"] = self.source_claim
        if self.target is not None:
            payload["target"] = self.target
        if self.type is not None:
            payload["type"] = self.type.value
        if self.strength is not None:
            payload["strength"] = self.strength
        if self.note is not None:
            payload["note"] = self.note
        if self.conditions_differ is not None:
            payload["conditions_differ"] = self.conditions_differ
        if self.resolution is not None:
            payload["resolution"] = self.resolution.to_payload()
        if self.target_justification_id is not None:
            payload["target_justification_id"] = self.target_justification_id
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload


class StanceFileDocument(DocumentStruct):
    source_claim: str
    stances: tuple[StanceEntryDocument, ...]
    classification_model: str | None = None
    classification_date: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_claim": self.source_claim,
            "stances": [stance.to_payload() for stance in self.stances],
        }
        if self.classification_model is not None:
            payload["classification_model"] = self.classification_model
        if self.classification_date is not None:
            payload["classification_date"] = self.classification_date
        return payload

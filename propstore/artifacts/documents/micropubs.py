"""Typed document models for Clark-style micropublications."""

from __future__ import annotations

from typing import Any

from propstore.artifacts.documents.claims import ClaimSourceDocument, ProvenanceDocument
from propstore.artifacts.documents.contexts import ContextReferenceDocument
from propstore.artifacts.schema import DocumentStruct
from propstore.stances import StanceType


class MicropublicationEvidenceDocument(DocumentStruct):
    kind: str
    reference: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "reference": self.reference,
        }


class MicropublicationDocument(DocumentStruct):
    artifact_id: str
    context: ContextReferenceDocument
    claims: tuple[str, ...]
    version_id: str | None = None
    evidence: tuple[MicropublicationEvidenceDocument, ...] = ()
    assumptions: tuple[str, ...] = ()
    stance: StanceType | None = None
    provenance: ProvenanceDocument | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.claims:
            raise ValueError("claims must contain at least one claim reference")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "context": self.context.to_payload(),
            "claims": list(self.claims),
        }
        if self.version_id is not None:
            payload["version_id"] = self.version_id
        if self.evidence:
            payload["evidence"] = [entry.to_payload() for entry in self.evidence]
        if self.assumptions:
            payload["assumptions"] = list(self.assumptions)
        if self.stance is not None:
            payload["stance"] = self.stance.value
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_payload()
        if self.source is not None:
            payload["source"] = self.source
        return payload


class MicropublicationsFileDocument(DocumentStruct):
    micropubs: tuple[MicropublicationDocument, ...]
    source: ClaimSourceDocument | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "micropubs": [micropub.to_payload() for micropub in self.micropubs],
        }
        if self.source is not None:
            payload["source"] = self.source.to_payload()
        return payload

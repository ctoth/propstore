"""Typed document models for canonical justification artifacts."""

from __future__ import annotations

from typing import Any

from quire.documents import DocumentStruct

from propstore.families.documents.sources import (
    SourceAttackTargetDocument,
    SourceProvenanceDocument,
)


class JustificationDocument(DocumentStruct):
    id: str | None = None
    conclusion: str | None = None
    premises: tuple[str, ...] = ()
    rule_kind: str | None = None
    rule_strength: str | None = None
    provenance: SourceProvenanceDocument | None = None
    attack_target: SourceAttackTargetDocument | None = None
    artifact_code: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.id is not None:
            payload["id"] = self.id
        if self.conclusion is not None:
            payload["conclusion"] = self.conclusion
        if self.premises:
            payload["premises"] = list(self.premises)
        if self.rule_kind is not None:
            payload["rule_kind"] = self.rule_kind
        if self.rule_strength is not None:
            payload["rule_strength"] = self.rule_strength
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_payload()
        if self.attack_target is not None:
            payload["attack_target"] = self.attack_target.to_payload()
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        return payload

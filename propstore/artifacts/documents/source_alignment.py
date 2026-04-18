"""Typed document models for concept-alignment artifacts."""

from __future__ import annotations

from typing import Any

from quire.documents import DocumentStruct


class AlignmentArgumentDocument(DocumentStruct):
    id: str
    source: str
    local_handle: str
    proposed_name: str
    proposed_uri: str
    definition: str
    form: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "local_handle": self.local_handle,
            "proposed_name": self.proposed_name,
            "proposed_uri": self.proposed_uri,
            "definition": self.definition,
            "form": self.form,
        }


class AlignmentFrameworkDocument(DocumentStruct):
    attacks: tuple[tuple[str, str], ...]
    ignorance: tuple[tuple[str, str], ...]
    non_attacks: tuple[tuple[str, str], ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "attacks": [list(pair) for pair in self.attacks],
            "ignorance": [list(pair) for pair in self.ignorance],
            "non_attacks": [list(pair) for pair in self.non_attacks],
        }


class AlignmentQueriesDocument(DocumentStruct):
    skeptical_acceptance: tuple[str, ...]
    credulous_acceptance: tuple[str, ...]
    operator_scores: dict[str, dict[str, int]]

    def to_payload(self) -> dict[str, Any]:
        return {
            "skeptical_acceptance": list(self.skeptical_acceptance),
            "credulous_acceptance": list(self.credulous_acceptance),
            "operator_scores": {
                operator: dict(scores)
                for operator, scores in self.operator_scores.items()
            },
        }


class AlignmentDecisionDocument(DocumentStruct):
    status: str
    accepted: tuple[str, ...]
    rejected: tuple[str, ...]
    promoted_concept: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "accepted": list(self.accepted),
            "rejected": list(self.rejected),
            "promoted_concept": self.promoted_concept,
        }
        return payload


class ConceptAlignmentArtifactDocument(DocumentStruct):
    kind: str
    id: str
    sources: tuple[str, ...]
    arguments: tuple[AlignmentArgumentDocument, ...]
    framework: AlignmentFrameworkDocument
    queries: AlignmentQueriesDocument
    decision: AlignmentDecisionDocument

    def to_payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "id": self.id,
            "sources": list(self.sources),
            "arguments": [argument.to_payload() for argument in self.arguments],
            "framework": self.framework.to_payload(),
            "queries": self.queries.to_payload(),
            "decision": self.decision.to_payload(),
        }

from __future__ import annotations

from typing import Any

from propstore.core.id_types import ClaimId, to_claim_id


class ResolutionTrace:
    """Accumulates worldline provenance across resolution phases."""

    def __init__(self) -> None:
        self.dependency_claims: set[ClaimId] = set()
        self.steps: list[dict[str, Any]] = []

    def record_binding(self, concept: str, value: Any) -> None:
        self.record_step(concept=concept, value=value, source="binding")

    def record_override(self, concept: str, value: Any) -> None:
        self.record_step(concept=concept, value=value, source="override")

    def record_step(self, **payload: Any) -> None:
        self.steps.append(dict(payload))

    def record_claim_dependency(self, claim_id: str | None) -> None:
        if claim_id and not claim_id.startswith("__override_"):
            self.dependency_claims.add(to_claim_id(claim_id))

    def record_claim_dependencies(self, claims: list[dict[str, Any]]) -> None:
        for claim in claims:
            claim_id = claim.get("id")
            if isinstance(claim_id, str):
                self.record_claim_dependency(claim_id)

    def seen_concepts(self) -> set[str]:
        return {
            concept
            for step in self.steps
            if isinstance((concept := step.get("concept")), str)
        }

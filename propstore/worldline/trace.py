from __future__ import annotations

from typing import Any

from propstore.core.active_claims import ActiveClaim
from propstore.core.id_types import ClaimId, to_claim_id
from propstore.worldline._constants import OVERRIDE_CLAIM_PREFIX
from propstore.worldline.result_types import WorldlineStep


class ResolutionTrace:
    """Accumulates worldline provenance across resolution phases."""

    def __init__(self) -> None:
        self.dependency_claims: set[ClaimId] = set()
        self.steps: list[WorldlineStep] = []

    def record_binding(self, concept: str, value: Any) -> None:
        self.record_step(concept=concept, value=value, source="binding")

    def record_override(self, concept: str, value: Any) -> None:
        self.record_step(concept=concept, value=value, source="override")

    def record_step(
        self,
        *,
        concept: str,
        source: str,
        value: Any = None,
        claim_id: str | None = None,
        strategy: str | None = None,
        reason: str | None = None,
        formula: str | None = None,
    ) -> None:
        self.steps.append(
            WorldlineStep(
                concept=concept,
                source=source,
                value=value,
                claim_id=claim_id,
                strategy=strategy,
                reason=reason,
                formula=formula,
            )
        )

    def record_claim_dependency(self, claim_id: str | None) -> None:
        if claim_id and not claim_id.startswith(OVERRIDE_CLAIM_PREFIX):
            self.dependency_claims.add(to_claim_id(claim_id))

    def record_claim_dependencies(self, claims: list[ActiveClaim]) -> None:
        for claim in claims:
            self.record_claim_dependency(str(claim.claim_id))

    def seen_concepts(self) -> set[str]:
        return {
            concept
            for step in self.steps
            if isinstance((concept := step.concept), str)
        }

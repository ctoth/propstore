"""Named result types for WorldStore and related world-query surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.core.id_types import ClaimId, ConceptId, to_claim_id, to_concept_id


@dataclass(frozen=True)
class ConceptSearchHit:
    concept_id: ConceptId

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


@dataclass(frozen=True)
class ClaimSimilarityHit:
    claim_id: ClaimId
    distance: float
    auto_summary: str | None = None
    statement: str | None = None
    source_paper: str | None = None
    concept_id: ConceptId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_id", to_claim_id(self.claim_id))
        if self.concept_id is not None:
            object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


@dataclass(frozen=True)
class ConceptSimilarityHit:
    concept_id: ConceptId
    distance: float
    primary_logical_id: str | None = None
    canonical_name: str | None = None
    definition: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))


@dataclass(frozen=True)
class WorldStoreStats:
    concepts: int
    claims: int
    conflicts: int

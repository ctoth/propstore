"""Named result types for WorldStore and related world-query surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from propstore.core.id_types import ClaimId, ConceptId, to_claim_id, to_concept_id


@dataclass(frozen=True)
class ConceptSearchHit:
    concept_id: ConceptId

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ConceptSearchHit:
        return cls(concept_id=data["concept_id"])


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

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ClaimSimilarityHit:
        return cls(
            claim_id=data["id"],
            distance=float(data["distance"]),
            auto_summary=None if data.get("auto_summary") is None else str(data["auto_summary"]),
            statement=None if data.get("statement") is None else str(data["statement"]),
            source_paper=None if data.get("source_paper") is None else str(data["source_paper"]),
            concept_id=data.get("concept_id"),
        )


@dataclass(frozen=True)
class ConceptSimilarityHit:
    concept_id: ConceptId
    distance: float
    primary_logical_id: str | None = None
    canonical_name: str | None = None
    definition: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_id", to_concept_id(self.concept_id))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ConceptSimilarityHit:
        return cls(
            concept_id=data["id"],
            distance=float(data["distance"]),
            primary_logical_id=(
                None if data.get("primary_logical_id") is None else str(data["primary_logical_id"])
            ),
            canonical_name=(
                None if data.get("canonical_name") is None else str(data["canonical_name"])
            ),
            definition=None if data.get("definition") is None else str(data["definition"]),
        )


@dataclass(frozen=True)
class WorldStoreStats:
    concepts: int
    claims: int
    conflicts: int

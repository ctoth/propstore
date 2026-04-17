"""Support evidence types for semiring provenance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from propstore.provenance.polynomial import ProvenancePolynomial


class SupportQuality(StrEnum):
    EXACT = "exact"
    SEMANTIC_COMPATIBLE = "semantic_compatible"
    CONTEXT_VISIBLE_ONLY = "context_visible_only"
    MIXED = "mixed"


@dataclass(frozen=True)
class SupportEvidence:
    polynomial: ProvenancePolynomial
    quality: SupportQuality

    def __post_init__(self) -> None:
        object.__setattr__(self, "quality", SupportQuality(self.quality))

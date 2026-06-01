"""Propstore metadata preference heuristics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from propstore.core.graph_types import ClaimNode
from propstore.families.claims.declaration import Claim
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


_METADATA_STRENGTH_BASE_RATE = 0.5


@dataclass(frozen=True)
class MetadataStrengthVector:
    """Metadata-derived preference strength plus its uncertainty.

    The dimensions are the Pareto-comparison coordinates used by the ASPIC+
    bridge. The opinion carries whether those coordinates are warranted; when
    metadata is missing, Jøsang 2001's vacuous opinion represents total
    ignorance instead of a fabricated finite preference strength.
    """

    dimensions: tuple[float, float, float]
    opinion: Opinion

    @property
    def uncertainty(self) -> float:
        return self.opinion.uncertainty

    @property
    def provenance(self) -> Provenance | None:
        return self.opinion.provenance

    @property
    def is_vacuous(self) -> bool:
        return self.uncertainty > 0.99


def _metadata_provenance(
    status: ProvenanceStatus, source_artifact_code: str
) -> Provenance:
    return Provenance(
        status=status,
        witnesses=(
            ProvenanceWitness(
                asserter="propstore.preference.metadata_strength_vector",
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                source_artifact_code=source_artifact_code,
                method="metadata_strength_vector",
            ),
        ),
        operations=("metadata_strength_vector",),
    )


def claim_strength(claim: Claim | ClaimNode) -> MetadataStrengthVector:
    """Return the propstore claim-graph metadata strength heuristic."""
    return metadata_strength_vector(claim)

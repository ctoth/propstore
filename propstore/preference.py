"""Propstore metadata preference heuristics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from propstore.core.active_claims import ActiveClaim
from propstore.opinion import Opinion, from_probability
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


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


def _metadata_provenance(status: ProvenanceStatus, source_artifact_code: str) -> Provenance:
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


def metadata_strength_vector(
    claim: ActiveClaim | Mapping[str, Any],
) -> MetadataStrengthVector:
    """Compute a heuristic fixed-length strength vector from claim metadata.

    Always returns exactly 3 dimensions so that Def 19 (Modgil & Prakken
    2018, p.21) Elitist/Democratic set comparisons are commensurable across
    claims with different metadata profiles. When explicit uncertainty is
    absent but sample size and confidence are present, uncertainty is derived
    through Jøsang 2001's evidence-to-opinion mapping (p.20-21). When metadata
    is insufficient even for that mapping, the vector is paired with a vacuous
    subjective-logic opinion so preference consumers can avoid treating absence
    of evidence as finite evidence.

    Fixed dimensions:
      [0] log_sample_size: log1p(sample_size)
      [1] inverse_uncertainty: 1/uncertainty
      [2] confidence: direct value
    """
    if isinstance(claim, ActiveClaim):
        sample_size = claim.sample_size
        uncertainty = claim.uncertainty
        confidence = claim.attributes.get("confidence")
        source_artifact_code = claim.artifact_id
    else:
        sample_size = claim.get("sample_size")
        uncertainty = claim.get("uncertainty")
        confidence = claim.get("confidence")
        source_artifact_code = str(claim.get("artifact_id") or "claim_metadata")

    sample_size_value = (
        float(sample_size)
        if isinstance(sample_size, int | float) and sample_size > 0
        else None
    )
    uncertainty_value = (
        float(uncertainty)
        if isinstance(uncertainty, int | float) and 0.0 < uncertainty <= 1.0
        else None
    )
    confidence_value = (
        float(confidence)
        if isinstance(confidence, int | float) and 0.0 <= confidence <= 1.0
        else None
    )

    provenance = _metadata_provenance(ProvenanceStatus.STATED, source_artifact_code)
    if (
        confidence_value is not None
        and sample_size_value is not None
        and uncertainty_value is None
    ):
        opinion = from_probability(
            confidence_value,
            sample_size_value,
            provenance=provenance,
        )
        uncertainty_value = opinion.uncertainty
    elif confidence_value is not None and uncertainty_value is not None:
        certainty = 1.0 - uncertainty_value
        opinion = Opinion(
            b=confidence_value * certainty,
            d=(1.0 - confidence_value) * certainty,
            u=uncertainty_value,
            a=0.5,
            provenance=provenance,
        )
    else:
        opinion = Opinion.vacuous(
            provenance=_metadata_provenance(
                ProvenanceStatus.VACUOUS,
                source_artifact_code,
            ),
        )

    dimensions = (
        math.log1p(sample_size_value) if sample_size_value is not None else 0.0,
        1.0 / uncertainty_value if uncertainty_value is not None else 0.0,
        confidence_value if confidence_value is not None else 0.0,
    )
    return MetadataStrengthVector(dimensions=dimensions, opinion=opinion)


def claim_strength(claim: ActiveClaim | Mapping[str, Any]) -> MetadataStrengthVector:
    """Return the propstore claim-graph metadata strength heuristic."""
    return metadata_strength_vector(claim)

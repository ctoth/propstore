"""Propstore metadata preference heuristics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from propstore.core.active_claims import ActiveClaim


def metadata_strength_vector(claim: ActiveClaim | Mapping[str, Any]) -> list[float]:
    """Compute a heuristic fixed-length strength vector from claim metadata.

    Always returns exactly 3 dimensions so that Def 19 (Modgil & Prakken
    2018, p.21) Elitist/Democratic set comparisons are commensurable across
    claims with different metadata profiles.

    Fixed dimensions:
      [0] log_sample_size: log1p(sample_size), default 0.0
      [1] inverse_uncertainty: 1/uncertainty, default 1.0
      [2] confidence: direct value, default 0.5
    """
    if isinstance(claim, ActiveClaim):
        sample_size = claim.sample_size
        uncertainty = claim.uncertainty
        confidence = claim.attributes.get("confidence")
    else:
        sample_size = claim.get("sample_size")
        uncertainty = claim.get("uncertainty")
        confidence = claim.get("confidence")
    return [
        math.log1p(sample_size) if sample_size and sample_size > 0 else 0.0,
        1.0 / uncertainty if uncertainty and uncertainty > 0 else 1.0,
        confidence if confidence is not None else 0.5,
    ]


def claim_strength(claim: ActiveClaim | Mapping[str, Any]) -> list[float]:
    """Return the propstore claim-graph metadata strength heuristic."""
    return metadata_strength_vector(claim)

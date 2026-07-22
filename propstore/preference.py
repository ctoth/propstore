"""Propstore metadata preference heuristics.

The ASPIC+ bridge compares claims by a fixed-length *strength vector* derived from
claim metadata (sample size, uncertainty, confidence). The heuristic is paired
with a subjective-logic opinion that says whether those coordinates are warranted:
when metadata is missing, Jøsang 2001's vacuous opinion (p.8) represents total
ignorance honestly instead of a fabricated finite preference strength
(CLAUDE.md "honest ignorance over fabricated confidence").

The opinion is ``doxa``'s canonical type used directly; its typed provenance rides
*beside* it on :class:`MetadataStrengthVector` (the pairing-beside-opinion
discipline), never baked into a re-spelled opinion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from doxa import Opinion

from propstore.core.active_claims import ActiveClaim
from propstore.families.claims import Claim
from propstore.provenance import Provenance, ProvenanceStatus

_METADATA_STRENGTH_BASE_RATE = 0.5
_DOGMATIC_TOL = 1e-9


@dataclass(frozen=True)
class MetadataStrengthVector:
    """Metadata-derived preference strength plus the opinion warranting it.

    :attr:`dimensions` are the Pareto-comparison coordinates used by the ASPIC+
    bridge. :attr:`opinion` is the ``doxa.Opinion`` carrying whether those
    coordinates are warranted, and :attr:`provenance` is the typed origin of that
    opinion's value — the pairing the honesty layer requires.
    """

    dimensions: tuple[float, float, float]
    opinion: Opinion
    provenance: Provenance

    @property
    def uncertainty(self) -> float:
        return self.opinion.uncertainty

    @property
    def is_vacuous(self) -> bool:
        return self.opinion.uncertainty > 0.99


def _stated_provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        operations=("metadata_strength_vector",),
    )


def _vacuous_provenance() -> Provenance:
    return Provenance(
        status=ProvenanceStatus.VACUOUS,
        operations=("metadata_strength_vector",),
    )


def _positive_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if value > 0 else None


def _unit_float(value: object, *, lower_inclusive: bool) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    lo_ok = value >= 0.0 if lower_inclusive else value > 0.0
    return float(value) if lo_ok and value <= 1.0 else None


def metadata_strength_vector(claim: Claim | ActiveClaim) -> MetadataStrengthVector:
    """Compute a heuristic fixed-length strength vector from claim metadata.

    Always returns exactly 3 dimensions so that Def 19 (Modgil & Prakken 2018,
    p.21) Elitist/Democratic set comparisons stay commensurable across claims with
    different metadata profiles. When explicit uncertainty is absent but sample
    size and confidence are present, uncertainty is derived through Jøsang 2001's
    evidence-to-opinion mapping (p.20-21). When metadata is insufficient even for
    that mapping, the vector is paired with a vacuous opinion so preference
    consumers never treat absence of evidence as finite evidence.

    Fixed dimensions:
      [0] log_sample_size: ``log1p(sample_size)``
      [1] inverse_uncertainty: ``1 / uncertainty``
      [2] confidence: direct value
    """

    sample_size_value = _positive_float(claim.sample_size)
    uncertainty_value = _unit_float(claim.uncertainty, lower_inclusive=False)
    confidence_value = _unit_float(claim.confidence, lower_inclusive=True)

    if (
        confidence_value is not None
        and sample_size_value is not None
        and uncertainty_value is None
    ):
        opinion = Opinion.from_probability(
            confidence_value,
            sample_size_value,
            _METADATA_STRENGTH_BASE_RATE,
        )
        uncertainty_value = opinion.uncertainty
        provenance = _stated_provenance()
    elif confidence_value is not None and uncertainty_value is not None:
        certainty = 1.0 - uncertainty_value
        opinion = Opinion(
            b=confidence_value * certainty,
            d=(1.0 - confidence_value) * certainty,
            u=uncertainty_value,
            a=_METADATA_STRENGTH_BASE_RATE,
            allow_dogmatic=uncertainty_value < _DOGMATIC_TOL,
        )
        provenance = _stated_provenance()
    else:
        opinion = Opinion.vacuous(_METADATA_STRENGTH_BASE_RATE)
        provenance = _vacuous_provenance()

    dimensions = (
        math.log1p(sample_size_value) if sample_size_value is not None else 0.0,
        1.0 / uncertainty_value if uncertainty_value is not None else 0.0,
        confidence_value if confidence_value is not None else 0.0,
    )
    return MetadataStrengthVector(
        dimensions=dimensions,
        opinion=opinion,
        provenance=provenance,
    )


def claim_strength(claim: Claim | ActiveClaim) -> MetadataStrengthVector:
    """Return the propstore claim-graph metadata strength heuristic."""

    return metadata_strength_vector(claim)

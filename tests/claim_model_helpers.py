from __future__ import annotations

import json
from collections.abc import Sequence

from propstore.core.algorithm_stage import AlgorithmStage
from propstore.families.claims.types import ClaimType
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import (
    Claim,
    ClaimAlgorithmPayload,
    ClaimConceptLink,
    ClaimNumericPayload,
    ClaimSourceAssertion,
    ClaimTextPayload,
)


def claim_concept_link(
    *,
    claim_id: str,
    concept_id: str,
    role: ClaimConceptLinkRole,
    ordinal: int = 0,
    binding_name: str | None = None,
) -> ClaimConceptLink:
    return ClaimConceptLink(
        claim_id=claim_id,
        concept_id=concept_id,
        role=role,
        ordinal=ordinal,
        binding_name=binding_name,
    )

"""Public ASPIC bridge facade."""

from propstore.grounding.complement import ComplementEncoder
from propstore.grounding.gunray_complement import GUNRAY_COMPLEMENT_ENCODER

from .build import build_bridge_csaf
from .grounding import grounded_rules_to_rules as _grounded_rules_to_rules
from .lifting_projection import (
    LiftingProjection,
    LiftingProjectionRecord,
    project_lifting_decisions,
)
from .projection import build_aspic_projection, csaf_to_projection
from .query import ClaimQueryResult, query_claim
from .translate import (
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    stances_to_contrariness,
)


def grounded_rules_to_rules(
    bundle,
    literals,
    *,
    complement_encoder: ComplementEncoder = GUNRAY_COMPLEMENT_ENCODER,
):
    return _grounded_rules_to_rules(
        bundle,
        literals,
        complement_encoder=complement_encoder,
    )

__all__ = [
    "ClaimQueryResult",
    "build_aspic_projection",
    "build_bridge_csaf",
    "build_preference_config",
    "claims_to_kb",
    "claims_to_literals",
    "csaf_to_projection",
    "grounded_rules_to_rules",
    "justifications_to_rules",
    "LiftingProjection",
    "LiftingProjectionRecord",
    "project_lifting_decisions",
    "query_claim",
    "stances_to_contrariness",
]

"""Public ASPIC bridge facade."""

from .build import build_bridge_csaf
from .grounding import grounded_rules_to_rules
from .projection import build_aspic_projection, csaf_to_projection
from .query import ClaimQueryResult, query_claim
from .translate import (
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    stances_to_contrariness,
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
    "query_claim",
    "stances_to_contrariness",
]

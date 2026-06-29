"""Claims/justifications/stances → ASPIC+ bridge.

The bridge translates the propstore claim graph into the argumentation package's
ASPIC+ types and runs its kernel, returning the package's own ``CSAF``. Every
stance and justification enters the system regardless of uncertainty — there is
no pre-render gate (CLAUDE.md non-commitment); resolution is a render-time concern
over the resulting framework.
"""

from propstore.aspic_bridge.build import (
    BridgeCompilation,
    build_bridge_csaf,
    compile_bridge_context,
)
from propstore.aspic_bridge.grounding import GroundedAspicProjection, project_grounded_rules
from propstore.aspic_bridge.lifting_projection import (
    LiftingProjection,
    LiftingProjectionRecord,
    project_lifting_decisions,
)
from propstore.aspic_bridge.query import ClaimQueryResult, query_claim
from propstore.aspic_bridge.translate import (
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    preference_sensitive_stance_pairs,
    stances_to_contrariness,
)

__all__ = [
    "BridgeCompilation",
    "ClaimQueryResult",
    "GroundedAspicProjection",
    "LiftingProjection",
    "LiftingProjectionRecord",
    "build_bridge_csaf",
    "build_preference_config",
    "claims_to_kb",
    "claims_to_literals",
    "compile_bridge_context",
    "justifications_to_rules",
    "preference_sensitive_stance_pairs",
    "project_grounded_rules",
    "project_lifting_decisions",
    "query_claim",
    "stances_to_contrariness",
]

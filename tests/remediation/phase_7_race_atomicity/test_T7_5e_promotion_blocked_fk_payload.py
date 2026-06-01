"""Regression test for promotion-blocked diagnostics with existing claim payloads.

Promotion-blocked source-local facts mirror blocked claim rows into
``claim_core`` unless an existing canonical ``claim_core`` row already owns the
claim id. In that case, the promotion-blocked flush must leave that canonical
row and its children in place while recording the blocking diagnostic.

Reproduces the Belch_2008 crash from the aspirin stance-backfill retry
session (2026-04-23): a claim was ingested in a sibling branch (so its
payload rows exist), and Belch's promote needed to mirror it as
blocked.
"""

from __future__ import annotations

from sqlalchemy import text

from propstore.families.claims.types import ClaimType
from propstore.families.claims.declaration import (
    compile_promotion_blocked_models,
)
from propstore.families.claims.stages import (
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from propstore.families.registry import world_schema
from quire.sqlalchemy_store import readonly_session, writable_session
from tests.remediation.phase_7_race_atomicity.promotion_blocked_helpers import (
    create_world_store,
    flush_promotion_blocked,
)

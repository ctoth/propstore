from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from tests.git_store_helpers import init_store
from tests.ws_l_merge_helpers import (
    claim_payloads_with_explicit_identities,
    obs_claim,
    snapshot,
)

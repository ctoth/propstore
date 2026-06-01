from __future__ import annotations

import yaml

from propstore.claims import claim_file_claims
from propstore.merge.merge_commit import create_merge_commit
from tests.git_store_helpers import init_store
from tests.family_helpers import load_claim_files
from tests.ws_l_merge_helpers import (
    claim_payloads_with_explicit_identities,
    obs_claim,
    snapshot,
)

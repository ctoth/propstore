from __future__ import annotations

import pytest

from propstore.merge.merge_commit import NonClaimMergeConflict, create_merge_commit
from tests.git_store_helpers import init_store
from tests.ws_l_merge_helpers import claim_payloads, obs_claim, snapshot

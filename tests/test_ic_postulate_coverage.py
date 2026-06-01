from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given
from hypothesis import HealthCheck
from hypothesis import settings
from hypothesis import strategies as st

from propstore.families.identity.claims import derive_claim_artifact_id
from propstore.merge.merge_classifier import IntegrityConstraint, build_merge_framework
from tests.git_store_helpers import init_store
from tests.ws_l_merge_helpers import claim_payloads, obs_claim, snapshot

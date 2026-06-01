"""WS-J Step 8/J-M2: epistemic snapshots detach from live state objects."""

from __future__ import annotations

from propstore.support_revision.snapshot_types import EpistemicStateSnapshot
from propstore.support_revision.iterated import make_epistemic_state
from tests.test_revision_operators import _base_with_shared_support

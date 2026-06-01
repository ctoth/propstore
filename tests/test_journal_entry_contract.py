"""WS-J Step 4a: transition journals store replay-dispatch contracts."""

from __future__ import annotations

import rfc8785
from propstore.support_revision.dispatch import dispatch
from propstore.support_revision.iterated import iterated_revise, make_epistemic_state
from propstore.support_revision.history import (
    TransitionJournalEntry,
    TransitionOperation,
)
from propstore.support_revision.snapshot_types import belief_atom_to_canonical_dict
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_iterated import _history_sensitive_base

from __future__ import annotations

from dataclasses import asdict

from belief_set import expand as formal_expand

from propstore.support_revision.belief_set_adapter import (
    decide_expand,
    project_formal_bundle,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_operators import _base_with_shared_support

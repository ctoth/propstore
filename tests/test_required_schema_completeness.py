"""Structural pin: required claim_core columns tracked by _REQUIRED_SCHEMA.

Canonical sidecar schema in ``propstore/sidecar/schema.py`` declares both
``content_hash`` and ``premise_kind`` on ``claim_core``. The validator in
``WorldModel._validate_schema`` only rejects sidecars missing columns that
appear in ``_REQUIRED_SCHEMA``; if a required column is absent from that
set, a pruned sidecar could load silently and surface the gap only at
query time. This test pins both columns as required at the module level.
"""

from __future__ import annotations

from propstore.world.model import _REQUIRED_SCHEMA


def test_content_hash_and_premise_kind_required_in_claim_core_schema() -> None:
    required_columns = _REQUIRED_SCHEMA["claim_core"]
    assert "content_hash" in required_columns, (
        "_REQUIRED_SCHEMA['claim_core'] is missing 'content_hash'; "
        f"current set: {sorted(required_columns)}"
    )
    assert "premise_kind" in required_columns, (
        "_REQUIRED_SCHEMA['claim_core'] is missing 'premise_kind'; "
        f"current set: {sorted(required_columns)}"
    )

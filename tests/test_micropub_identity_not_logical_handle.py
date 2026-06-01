from __future__ import annotations

from propstore.source import finalize


def test_old_source_claim_handle_identity_surface_is_deleted() -> None:
    assert not hasattr(finalize, "_stable_micropub_artifact_id")
    assert not hasattr(finalize, "_stamp_micropub_identity")

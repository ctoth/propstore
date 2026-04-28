"""WS-J Step 8 adjacent: revision capture never returns a live state object."""

from __future__ import annotations

import pytest

from propstore.worldline.revision_capture import _revision_state_snapshot


def test_ws_j_revision_capture_rejects_live_state_to_dict_fallback() -> None:
    class _LiveState:
        def to_dict(self):
            return {"content_hash": "live"}

    with pytest.raises(TypeError, match="revision_state_snapshot"):
        _revision_state_snapshot(object(), _LiveState())

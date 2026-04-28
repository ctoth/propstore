"""WS-J Step 8/J-M1: worldline content hashes expose 128 bits."""

from __future__ import annotations

import re

from propstore.worldline import compute_worldline_content_hash
from propstore.worldline.result_types import WorldlineDependencies, WorldlineTargetValue


def test_ws_j_worldline_content_hash_is_32_hex_chars() -> None:
    digest = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=None,
    )

    assert re.fullmatch(r"[0-9a-f]{32}", digest) is not None

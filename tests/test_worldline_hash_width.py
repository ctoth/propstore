"""WS-M D-20: worldline content hashes store full SHA-256 identity."""

from __future__ import annotations

import re

from propstore.worldline import compute_worldline_content_hash
from propstore.worldline.result_types import WorldlineDependencies, WorldlineTargetValue


def test_worldline_content_hash_is_full_sha256_hex() -> None:
    digest = compute_worldline_content_hash(
        values={"target": WorldlineTargetValue(status="determined", value=1.0)},
        steps=(),
        dependencies=WorldlineDependencies(),
        sensitivity=None,
        argumentation=None,
        revision=None,
    )

    assert re.fullmatch(r"[0-9a-f]{64}", digest) is not None

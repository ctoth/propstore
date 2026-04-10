from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
)


def compute_worldline_content_hash(
    *,
    values: Mapping[str, WorldlineTargetValue],
    steps: Sequence[WorldlineStep],
    dependencies: WorldlineDependencies,
    sensitivity: WorldlineSensitivityReport | None,
    argumentation: WorldlineArgumentationState | None,
    revision: dict[str, Any] | None,
) -> str:
    """Compute a deterministic fingerprint for materialized worldline content."""
    payload = {
        "values": {
            target_name: target_value.to_dict()
            for target_name, target_value in values.items()
        },
        "steps": [step.to_dict() for step in steps],
        "dependencies": dependencies.to_dict(),
        "sensitivity": None if sensitivity is None else sensitivity.to_dict(),
        "argumentation": None if argumentation is None else argumentation.to_dict(),
        "revision": revision,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]

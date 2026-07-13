from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from quire.canonical import canonical_json_bytes

from propstore.reporting import json_ready
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityReport,
    WorldlineStep,
    WorldlineTargetValue,
)
from propstore.worldline.revision_types import WorldlineRevisionState


def compute_worldline_content_hash(
    *,
    values: Mapping[str, WorldlineTargetValue],
    steps: Sequence[WorldlineStep],
    dependencies: WorldlineDependencies,
    sensitivity: WorldlineSensitivityReport | None,
    argumentation: WorldlineArgumentationState | None,
    revision: WorldlineRevisionState | None,
    policy: Mapping[str, object] | None = None,
) -> str:
    """Compute a deterministic fingerprint for materialized worldline content.

    Identity is the canonical JSON of the rendered content (quire's canonical
    encoder), digested to a bare 64-char SHA-256 hex. The typed content is
    lowered by :func:`json_ready`, so the fingerprint is derived from the render
    types themselves rather than from a hand-written serialization that could
    drift from them. Transient capture failures are recorded as typed error
    markers, never as exception text, so equivalent failures hash identically.
    """
    payload = {
        "policy": {} if policy is None else dict(policy),
        "values": json_ready(values),
        "steps": json_ready(list(steps)),
        "dependencies": json_ready(dependencies),
        "sensitivity": json_ready(sensitivity),
        "argumentation": json_ready(argumentation),
        "revision": json_ready(revision),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

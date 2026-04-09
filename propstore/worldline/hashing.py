from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_worldline_content_hash(
    *,
    values: dict[str, dict[str, Any]],
    steps: list[dict[str, Any]],
    dependencies: dict[str, list[str]],
    sensitivity: dict[str, Any] | None,
    argumentation: dict[str, Any] | None,
    revision: dict[str, Any] | None,
) -> str:
    """Compute a deterministic fingerprint for materialized worldline content."""
    payload = {
        "values": values,
        "steps": steps,
        "dependencies": dependencies,
        "sensitivity": sensitivity,
        "argumentation": argumentation,
        "revision": revision,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]

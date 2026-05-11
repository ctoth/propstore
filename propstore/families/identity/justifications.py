from __future__ import annotations

import copy
from typing import Any

from propstore.artifact_codes import justification_artifact_code
from propstore.json_types import JsonObject

JUSTIFICATION_VERSION_ID_EXCLUDED_FIELDS = ("artifact_code",)


def canonicalize_justification_for_identity(justification: JsonObject) -> JsonObject:
    canonical = copy.deepcopy(justification)
    for field in JUSTIFICATION_VERSION_ID_EXCLUDED_FIELDS:
        canonical.pop(field, None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = [str(premise) for premise in sorted(premises, key=str)]
    return canonical


def derive_justification_artifact_id(justification: JsonObject) -> str:
    artifact_id = justification.get("artifact_code")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return justification_artifact_code(canonicalize_justification_for_identity(justification))


def stamp_justification_artifact_id(justification: dict[str, Any]) -> JsonObject:
    stamped: JsonObject = copy.deepcopy(justification)
    stamped["artifact_code"] = derive_justification_artifact_id(stamped)
    return stamped

from __future__ import annotations

import copy
from typing import Any

from quire import canonical_json_sha256

from propstore.json_types import JsonObject
from propstore.stances import StanceType

STANCE_VERSION_ID_EXCLUDED_FIELDS = (
    "artifact_id",
    "artifact_code",
    "classification_date",
    "classification_model",
    "promoted_from_sha",
)


def canonicalize_stance_for_identity(stance: JsonObject) -> JsonObject:
    canonical = copy.deepcopy(stance)
    for field in STANCE_VERSION_ID_EXCLUDED_FIELDS:
        canonical.pop(field, None)
    for field in tuple(canonical):
        if canonical[field] is None:
            canonical.pop(field)
    stance_type = canonical.get("type")
    if isinstance(stance_type, StanceType):
        canonical["type"] = stance_type.value
    return canonical


def derive_stance_artifact_id(stance: JsonObject) -> str:
    artifact_id = stance.get("artifact_code")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return canonical_json_sha256(canonicalize_stance_for_identity(stance))


def stamp_stance_artifact_id(stance: dict[str, Any]) -> JsonObject:
    stamped: JsonObject = copy.deepcopy(stance)
    artifact_id = derive_stance_artifact_id(stamped)
    stamped["artifact_code"] = artifact_id
    stamped["artifact_id"] = artifact_id
    return stamped

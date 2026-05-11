from __future__ import annotations

import copy
from typing import Any

from quire.documents import convert_document_value

from propstore.artifact_codes import stance_artifact_code
from propstore.families.documents.stances import StanceDocument
from propstore.json_types import JsonObject

STANCE_VERSION_ID_EXCLUDED_FIELDS = (
    "artifact_code",
    "classification_date",
    "classification_model",
    "promoted_from_sha",
)


def canonicalize_stance_for_identity(stance: JsonObject) -> JsonObject:
    canonical = copy.deepcopy(stance)
    for field in STANCE_VERSION_ID_EXCLUDED_FIELDS:
        canonical.pop(field, None)
    return canonical


def derive_stance_artifact_id(stance: JsonObject) -> str:
    artifact_id = stance.get("artifact_code")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    document = convert_document_value(
        canonicalize_stance_for_identity(stance),
        StanceDocument,
        source="stance-identity",
    )
    return stance_artifact_code(document)


def stamp_stance_artifact_id(stance: dict[str, Any]) -> JsonObject:
    stamped: JsonObject = copy.deepcopy(stance)
    stamped["artifact_code"] = derive_stance_artifact_id(stamped)
    return stamped

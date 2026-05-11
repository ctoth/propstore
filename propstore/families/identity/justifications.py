from __future__ import annotations

import copy
from typing import Any

from quire.documents import convert_document_value

from propstore.artifact_codes import justification_artifact_code
from propstore.families.documents.justifications import JustificationDocument
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
    document = convert_document_value(
        canonicalize_justification_for_identity(justification),
        JustificationDocument,
        source="justification-identity",
    )
    return justification_artifact_code(document)


def stamp_justification_artifact_id(justification: dict[str, Any]) -> JsonObject:
    stamped: JsonObject = copy.deepcopy(justification)
    stamped["artifact_code"] = derive_justification_artifact_id(stamped)
    return stamped

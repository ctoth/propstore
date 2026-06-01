from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quire.documents import convert_document_value
from quire.references import FamilyReferenceIndex

from propstore.canonical_namespaces import assert_namespace_not_reserved
from propstore.families.claims.declaration import (
    ClaimDocument,
    SourceClaimDocument,
)
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.identity.claims import (
    normalize_claim_file_payload,
)


@dataclass(frozen=True)
class NormalizedImportedClaimArtifact:
    document: ClaimDocument
    local_handle_map: dict[str, str]


@dataclass(frozen=True)
class NormalizedPromotedClaimArtifact:
    document: ClaimDocument


def source_concept_ref_requires_mapping(value: str) -> bool:
    return not (value.startswith("ps:concept:") or value.startswith("tag:"))


def _normalize_source_claim_namespace(source_namespace: str) -> str:
    namespace = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_"
        for ch in source_namespace.strip()
    )
    namespace = namespace.strip("._-") or "source"
    assert_namespace_not_reserved(namespace, context="source claims namespace")
    return namespace


def _require_source_or_primary_claim_id(
    reference: object,
    *,
    source: FamilyReferenceIndex[SourceClaimDocument],
    primary: FamilyReferenceIndex[Any] | None,
) -> str:
    resolved = resolve_first_claim_reference_id(
        reference,
        source,
        primary,
    )
    if resolved is None:
        if not isinstance(reference, str) or not reference:
            raise ValueError("claim reference must be a non-empty string")
        source.require_id(reference)
        raise AssertionError("unreachable")
    return resolved

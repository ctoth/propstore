from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from quire.documents import convert_document_value, document_to_payload
from quire.references import FamilyReferenceIndex

from propstore.canonical_namespaces import assert_namespace_not_reserved
from propstore.families.claims.declaration import (
    ClaimDocument,
    ClaimLogicalIdDocument,
    SourceClaimDocument,
    SourceJustificationDocument,
)
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.identity.claims import (
    compute_claim_version_id,
    derive_claim_artifact_id,
    normalize_canonical_claim_payload,
    normalize_claim_file_payload,
)
from propstore.families.identity.logical_ids import normalize_logical_value


@dataclass(frozen=True)
class NormalizedImportedClaimArtifact:
    document: ClaimDocument
    local_handle_map: dict[str, str]


@dataclass(frozen=True)
class NormalizedPromotedClaimArtifact:
    document: ClaimDocument


def source_concept_ref_requires_mapping(value: str) -> bool:
    return not (value.startswith("ps:concept:") or value.startswith("tag:"))


def stable_claim_logical_value(claim: SourceClaimDocument, *, source_uri: str) -> str:
    canonical = cast(dict[str, Any], document_to_payload(claim))
    canonical.pop("id", None)
    canonical.pop("artifact_id", None)
    canonical.pop("version_id", None)
    canonical.pop("logical_ids", None)
    canonical.pop("source_local_id", None)
    payload = json.dumps(
        {"source_uri": source_uri, "claim": canonical},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"claim_{digest}"


def rewrite_imported_claim_concept_refs(
    payload: Mapping[str, Any],
    concept_map: Mapping[str, str],
    *,
    unresolved: set[str],
) -> dict[str, Any]:
    return _rewrite_claim_concept_payload(
        dict(payload),
        concept_map,
        unresolved=unresolved,
    )


def rewrite_source_claim_concept_refs(
    claim: SourceClaimDocument,
    concept_map: Mapping[str, str],
    *,
    unresolved: set[str],
) -> dict[str, Any]:
    payload = document_to_payload(claim)
    if not isinstance(payload, dict):
        raise TypeError("source claim payload must be a mapping")
    return _rewrite_claim_concept_payload(
        cast(dict[str, Any], payload),
        concept_map,
        unresolved=unresolved,
    )


def normalize_imported_claim_artifact(
    payload: Mapping[str, Any],
    *,
    default_namespace: str,
    default_source: Mapping[str, str] | None,
    concept_map: Mapping[str, str],
    source: str,
) -> NormalizedImportedClaimArtifact:
    normalized_input: dict[str, Any] = {"claims": [dict(payload)]}
    source_payload = payload.get("source")
    has_source = (
        isinstance(source_payload, dict)
        and isinstance(source_payload.get("paper"), str)
        and bool(source_payload.get("paper"))
    )
    if has_source:
        normalized_input["source"] = source_payload
    normalized_payload, local_map = normalize_claim_file_payload(
        normalized_input,
        default_namespace=default_namespace,
    )
    normalized_claims = normalized_payload.get("claims")
    if not isinstance(normalized_claims, list) or len(normalized_claims) != 1:
        raise ValueError(
            f"Imported claim path {source!r} did not normalize to one claim artifact"
        )
    normalized_claim = normalized_claims[0]
    if not isinstance(normalized_claim, dict):
        raise ValueError(
            f"Imported claim path {source!r} did not normalize to a claim mapping"
        )
    if not has_source and default_source is not None:
        normalized_claim["source"] = dict(default_source)
    rewritten_payload = rewrite_imported_claim_concept_refs(
        normalized_claim,
        concept_map,
        unresolved=set(),
    )
    return NormalizedImportedClaimArtifact(
        document=convert_document_value(
            rewritten_payload,
            ClaimDocument,
            source=source,
        ),
        local_handle_map=local_map,
    )


def normalize_promoted_source_claim_artifact(
    claim: SourceClaimDocument,
    *,
    source_paper: str,
    concept_map: Mapping[str, str],
    unresolved: set[str],
    source: str,
) -> NormalizedPromotedClaimArtifact:
    rewritten_payload = rewrite_source_claim_concept_refs(
        claim,
        concept_map,
        unresolved=unresolved,
    )
    provenance = rewritten_payload.get("provenance")
    if isinstance(provenance, dict) and not isinstance(provenance.get("paper"), str):
        rewritten_payload["provenance"] = {
            **provenance,
            "paper": source_paper,
        }
    context = rewritten_payload.get("context")
    if isinstance(context, str):
        rewritten_payload["context"] = {"id": context}
    rewritten_payload.setdefault("source", {"paper": source_paper})
    normalized_payload = normalize_canonical_claim_payload(
        rewritten_payload,
        strip_source_local=True,
    )
    normalized_document = convert_document_value(
        normalized_payload,
        ClaimDocument,
        source=source,
    )
    document_payload = document_to_payload(normalized_document)
    if not isinstance(document_payload, dict):
        raise TypeError("promoted claim document payload must be a mapping")
    document_payload["version_id"] = compute_claim_version_id(document_payload)
    return NormalizedPromotedClaimArtifact(
        document=convert_document_value(
            document_payload,
            ClaimDocument,
            source=source,
        ),
    )


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

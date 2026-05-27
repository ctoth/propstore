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


def normalize_source_claims_payload(
    data: tuple[SourceClaimDocument, ...],
    *,
    source_uri: str,
    source_namespace: str,
) -> tuple[tuple[SourceClaimDocument, ...], dict[str, str]]:
    normalized_claims: list[SourceClaimDocument] = []
    local_to_canonical: dict[str, str] = {}
    namespace = _normalize_source_claim_namespace(source_namespace)

    for index, claim in enumerate(data, start=1):
        normalized = cast(dict[str, Any], document_to_payload(claim))
        raw_local_id = claim.source_local_id or claim.id
        stable_value = stable_claim_logical_value(claim, source_uri=source_uri)
        normalized["id"] = stable_value
        normalized.pop("artifact_code", None)
        logical_ids = [ClaimLogicalIdDocument(namespace=namespace, value=stable_value)]
        if isinstance(raw_local_id, str) and raw_local_id:
            normalized["source_local_id"] = raw_local_id
            local_to_canonical[raw_local_id] = stable_value
            local_value = normalize_logical_value(raw_local_id)
            if local_value != stable_value:
                logical_ids.append(
                    ClaimLogicalIdDocument(namespace=namespace, value=local_value)
                )
        else:
            normalized.pop("source_local_id", None)
        normalized["logical_ids"] = logical_ids
        normalized["artifact_id"] = derive_claim_artifact_id(namespace, stable_value)
        normalized["version_id"] = compute_claim_version_id(
            {
                **normalized,
                "logical_ids": [
                    document_to_payload(logical_id) for logical_id in logical_ids
                ],
            }
        )
        normalized_claims.append(
            convert_document_value(
                normalized,
                SourceClaimDocument,
                source=f"{source_namespace}:claims[{index}]",
            )
        )

    return (
        tuple(normalized_claims),
        local_to_canonical,
    )


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
    normalized_payload = normalize_canonical_claim_payload(
        rewritten_payload,
        strip_source_local=True,
    )
    normalized_payload.setdefault("source", {"paper": source_paper})
    return NormalizedPromotedClaimArtifact(
        document=convert_document_value(
            normalized_payload,
            ClaimDocument,
            source=source,
        ),
    )


def normalize_source_justifications_payload(
    data: tuple[SourceJustificationDocument, ...],
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Any] | None = None,
) -> tuple[SourceJustificationDocument, ...]:
    normalized_justifications: list[SourceJustificationDocument] = []
    for index, justification in enumerate(data, start=1):
        if justification.conclusion is None:
            raise ValueError("justification conclusion must be a non-empty string")
        normalized = cast(dict[str, Any], document_to_payload(justification))
        normalized["conclusion"] = _require_source_or_primary_claim_id(
            justification.conclusion,
            source=claim_index,
            primary=primary_claim_index,
        )
        normalized["premises"] = [
            _require_source_or_primary_claim_id(
                premise,
                source=claim_index,
                primary=primary_claim_index,
            )
            for premise in justification.premises
        ]
        attack_target = justification.attack_target
        if attack_target is not None and attack_target.target_claim is not None:
            updated_target = cast(dict[str, Any], document_to_payload(attack_target))
            updated_target["target_claim"] = _require_source_or_primary_claim_id(
                attack_target.target_claim,
                source=claim_index,
                primary=primary_claim_index,
            )
            normalized["attack_target"] = updated_target
        normalized_justifications.append(
            convert_document_value(
                normalized,
                SourceJustificationDocument,
                source=f"justifications[{index}]",
            )
        )
    return tuple(normalized_justifications)


def _normalize_source_claim_namespace(source_namespace: str) -> str:
    namespace = "".join(
        ch if ch.isalnum() or ch in {"_", "-", "."} else "_"
        for ch in source_namespace.strip()
    )
    namespace = namespace.strip("._-") or "source"
    assert_namespace_not_reserved(namespace, context="source claims namespace")
    return namespace


def _rewrite_claim_concept_payload(
    payload: dict[str, Any],
    concept_map: Mapping[str, str],
    *,
    unresolved: set[str],
) -> dict[str, Any]:
    normalized = dict(payload)

    def resolve(value: object) -> object:
        if not isinstance(value, str):
            return value
        if not source_concept_ref_requires_mapping(value):
            return value
        resolved = concept_map.get(value)
        if resolved is None:
            unresolved.add(value)
            return value
        return resolved

    if "concept" in normalized:
        concept = resolve(normalized.pop("concept"))
        claim_type = normalized.get("type")
        if claim_type in {"parameter", "algorithm"} and "output_concept" not in normalized:
            normalized["output_concept"] = concept
        elif claim_type == "measurement" and "target_concept" not in normalized:
            normalized["target_concept"] = concept
        else:
            concepts = normalized.get("concepts")
            merged_concepts = list(concepts) if isinstance(concepts, list) else []
            if concept not in merged_concepts:
                merged_concepts.insert(0, concept)
            normalized["concepts"] = merged_concepts
    if "output_concept" in normalized:
        normalized["output_concept"] = resolve(normalized.get("output_concept"))
    if "target_concept" in normalized:
        normalized["target_concept"] = resolve(normalized.get("target_concept"))
    if isinstance(normalized.get("concepts"), list):
        normalized["concepts"] = [resolve(value) for value in normalized["concepts"]]
    if isinstance(normalized.get("variables"), list):
        for variable in normalized["variables"]:
            if isinstance(variable, dict):
                variable["concept"] = resolve(variable.get("concept"))
    if isinstance(normalized.get("parameters"), list):
        for parameter in normalized["parameters"]:
            if isinstance(parameter, dict):
                parameter["concept"] = resolve(parameter.get("concept"))
    return normalize_canonical_claim_payload(normalized)


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

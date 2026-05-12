from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quire.documents import convert_document_value

from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.sources import SourceClaimDocument
from propstore.families.identity.claims import (
    normalize_canonical_claim_payload,
    normalize_claim_file_payload,
)


ClaimConceptSource = ClaimDocument | SourceClaimDocument | Mapping[str, Any]


@dataclass(frozen=True)
class NormalizedImportedClaimArtifact:
    document: ClaimDocument
    local_handle_map: dict[str, str]


def source_concept_ref_requires_mapping(value: str) -> bool:
    return not (value.startswith("ps:concept:") or value.startswith("tag:"))


def rewrite_claim_concept_refs(
    claim: ClaimConceptSource,
    concept_map: Mapping[str, str],
    *,
    unresolved: set[str],
) -> dict[str, Any]:
    normalized = _claim_payload(claim)

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
        _place_source_local_concept(normalized, concept)
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
        raise ValueError(f"Imported claim path {source!r} did not normalize to one claim artifact")
    normalized_claim = normalized_claims[0]
    if not isinstance(normalized_claim, dict):
        raise ValueError(f"Imported claim path {source!r} did not normalize to a claim mapping")
    if not has_source and default_source is not None:
        normalized_claim["source"] = dict(default_source)
    rewritten_payload = rewrite_claim_concept_refs(
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


def _claim_payload(claim: ClaimConceptSource) -> dict[str, Any]:
    if isinstance(claim, ClaimDocument | SourceClaimDocument):
        return claim.to_payload()
    return copy.deepcopy(dict(claim))


def _place_source_local_concept(claim: dict[str, Any], concept: object) -> None:
    claim_type = claim.get("type")
    if claim_type in {"parameter", "algorithm"} and "output_concept" not in claim:
        claim["output_concept"] = concept
        return
    if claim_type == "measurement" and "target_concept" not in claim:
        claim["target_concept"] = concept
        return
    concepts = claim.get("concepts")
    merged_concepts = list(concepts) if isinstance(concepts, list) else []
    if concept not in merged_concepts:
        merged_concepts.insert(0, concept)
    claim["concepts"] = merged_concepts

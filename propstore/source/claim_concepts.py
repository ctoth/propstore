from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.sources import SourceClaimDocument
from propstore.families.identity.claims import normalize_canonical_claim_payload


ClaimConceptSource = ClaimDocument | SourceClaimDocument | Mapping[str, Any]


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

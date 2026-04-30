"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any

from quire.hashing import canonical_json_sha256

from propstore.families.identity.claims import canonicalize_claim_for_version


def _hash_payload(payload: dict[str, Any]) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: dict[str, Any]) -> str:
    canonical = copy.deepcopy(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(justification: dict[str, Any]) -> str:
    canonical = copy.deepcopy(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = sorted(str(premise) for premise in premises)
    return _hash_payload(canonical)


def stance_artifact_code(stance: dict[str, Any]) -> str:
    canonical = copy.deepcopy(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def claim_artifact_code(
    claim: dict[str, Any],
    *,
    source_code: str,
    justification_codes: list[str],
    stance_codes: list[str],
) -> str:
    canonical = canonicalize_claim_for_version(claim)
    canonical.pop("artifact_code", None)
    return _hash_payload(
        {
            "source_artifact_code": source_code,
            "claim": canonical,
            "justification_codes": sorted(justification_codes),
            "stance_codes": sorted(stance_codes),
        }
    )


def attach_source_artifact_codes(
    source_doc: dict[str, Any],
    claims_doc: dict[str, Any] | None,
    justifications_doc: dict[str, Any] | None,
    stances_doc: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    updated_source = copy.deepcopy(source_doc)
    updated_claims = copy.deepcopy(claims_doc or {"claims": []})
    updated_justifications = copy.deepcopy(justifications_doc or {"justifications": []})
    updated_stances = copy.deepcopy(stances_doc or {"stances": []})

    source_code = source_artifact_code(updated_source)
    updated_source["artifact_code"] = source_code

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[Any] = []
    for justification in updated_justifications.get("justifications", []) or []:
        if not isinstance(justification, dict):
            rewritten_justifications.append(justification)
            continue
        rewritten = copy.deepcopy(justification)
        rewritten["artifact_code"] = justification_artifact_code(rewritten)
        conclusion = rewritten.get("conclusion")
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(rewritten["artifact_code"])
        rewritten_justifications.append(rewritten)
    updated_justifications["justifications"] = rewritten_justifications

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[Any] = []
    for stance in updated_stances.get("stances", []) or []:
        if not isinstance(stance, dict):
            rewritten_stances.append(stance)
            continue
        rewritten = copy.deepcopy(stance)
        rewritten["artifact_code"] = stance_artifact_code(rewritten)
        source_claim = rewritten.get("source_claim")
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(rewritten["artifact_code"])
        rewritten_stances.append(rewritten)
    updated_stances["stances"] = rewritten_stances

    rewritten_claims: list[Any] = []
    for claim in updated_claims.get("claims", []) or []:
        if not isinstance(claim, dict):
            rewritten_claims.append(claim)
            continue
        rewritten = copy.deepcopy(claim)
        claim_id = rewritten.get("artifact_id")
        justification_codes = justification_codes_by_conclusion.get(str(claim_id), [])
        stance_codes = stance_codes_by_source.get(str(claim_id), [])
        rewritten["artifact_code"] = claim_artifact_code(
            rewritten,
            source_code=source_code,
            justification_codes=justification_codes,
            stance_codes=stance_codes,
        )
        rewritten_claims.append(rewritten)
    updated_claims["claims"] = rewritten_claims
    return updated_source, updated_claims, updated_justifications, updated_stances

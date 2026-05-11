"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

import copy
from collections import defaultdict

from quire.hashing import canonical_json_sha256

from propstore.families.identity.claims import canonicalize_claim_for_version
from propstore.json_types import JsonObject, JsonValue


def _hash_payload(payload: JsonObject) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: JsonObject) -> str:
    canonical = copy.deepcopy(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(justification: JsonObject) -> str:
    canonical = copy.deepcopy(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = [
            str(premise)
            for premise in sorted(premises, key=str)
        ]
    return _hash_payload(canonical)


def stance_artifact_code(stance: JsonObject) -> str:
    canonical = copy.deepcopy(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def _copied_artifact_doc(
    payload: JsonObject | None,
    *,
    list_field: str,
) -> JsonObject:
    if payload is not None:
        return copy.deepcopy(payload)
    return {list_field: []}


def _artifact_entries(payload: JsonObject, list_field: str) -> list[JsonValue]:
    entries = payload.get(list_field)
    return entries if isinstance(entries, list) else []


def claim_artifact_code(
    claim: JsonObject,
    *,
    source_code: str,
    justification_codes: list[str],
    stance_codes: list[str],
) -> str:
    canonical = canonicalize_claim_for_version(claim)
    canonical.pop("artifact_code", None)
    payload: JsonObject = {
        "source_artifact_code": source_code,
        "claim": canonical,
        "justification_codes": [
            code for code in sorted(justification_codes)
        ],
        "stance_codes": [
            code for code in sorted(stance_codes)
        ],
    }
    return _hash_payload(
        payload
    )


def attach_source_artifact_codes(
    source_doc: JsonObject,
    claims_doc: JsonObject | None,
    justifications_doc: JsonObject | None,
    stances_doc: JsonObject | None,
) -> tuple[JsonObject, JsonObject, JsonObject, JsonObject]:
    updated_source = copy.deepcopy(source_doc)
    updated_claims = _copied_artifact_doc(claims_doc, list_field="claims")
    updated_justifications = _copied_artifact_doc(
        justifications_doc,
        list_field="justifications",
    )
    updated_stances = _copied_artifact_doc(stances_doc, list_field="stances")

    source_code = source_artifact_code(updated_source)
    updated_source["artifact_code"] = source_code

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[JsonValue] = []
    for justification in _artifact_entries(updated_justifications, "justifications"):
        if not isinstance(justification, dict):
            rewritten_justifications.append(justification)
            continue
        rewritten = copy.deepcopy(justification)
        artifact_code = justification_artifact_code(rewritten)
        rewritten["artifact_code"] = artifact_code
        conclusion = rewritten.get("conclusion")
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)
    updated_justifications["justifications"] = rewritten_justifications

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[JsonValue] = []
    for stance in _artifact_entries(updated_stances, "stances"):
        if not isinstance(stance, dict):
            rewritten_stances.append(stance)
            continue
        rewritten = copy.deepcopy(stance)
        artifact_code = stance_artifact_code(rewritten)
        rewritten["artifact_code"] = artifact_code
        source_claim = rewritten.get("source_claim")
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)
    updated_stances["stances"] = rewritten_stances

    rewritten_claims: list[JsonValue] = []
    for claim in _artifact_entries(updated_claims, "claims"):
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

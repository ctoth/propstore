"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

import copy
from collections import defaultdict

from quire.hashing import canonical_json_sha256

from propstore.families.identity.claims import canonicalize_claim_for_version


def _hash_payload(payload: dict[str, object]) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: dict[str, object]) -> str:
    canonical = copy.deepcopy(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(justification: dict[str, object]) -> str:
    canonical = copy.deepcopy(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = sorted(str(premise) for premise in premises)
    return _hash_payload(canonical)


def stance_artifact_code(stance: dict[str, object]) -> str:
    canonical = copy.deepcopy(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def _copied_artifact_doc(
    payload: dict[str, object] | None,
    *,
    list_field: str,
) -> dict[str, object]:
    if payload is not None:
        return copy.deepcopy(payload)
    return {list_field: []}


def _artifact_entries(payload: dict[str, object], list_field: str) -> list[object]:
    entries = payload.get(list_field)
    return entries if isinstance(entries, list) else []


def claim_artifact_code(
    claim: dict[str, object],
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
    source_doc: dict[str, object],
    claims_doc: dict[str, object] | None,
    justifications_doc: dict[str, object] | None,
    stances_doc: dict[str, object] | None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
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
    rewritten_justifications: list[object] = []
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
    rewritten_stances: list[object] = []
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

    rewritten_claims: list[object] = []
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

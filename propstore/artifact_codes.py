"""Semantic artifact-code stamping for source-branch proposals.

An *artifact code* is a deterministic content hash stamped onto each proposed
source artifact (the source manifest, its claims, justifications, and stances) at
finalize time. Unlike the claim ``artifact_id`` — an ``ni:``/``ps:`` trusty
handle derived from the claim's *logical* identity — the artifact code is a hash
of the artifact's *content* (with the recursive ``artifact_code`` field itself
excluded), so it changes whenever the proposal's content changes. A claim's code
additionally folds in the source code and the codes of the justifications and
stances that bear on it, so a claim's code captures the proposal slice that
produced it.

Identity excludes provenance only in the trusty-URI sense (the ``artifact_id``
is derived from the logical handle, not the content); the artifact *code* is a
content hash and intentionally covers every authored field, matching the
reference behaviour.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TypeGuard

import msgspec

from quire.canonical import canonical_json_sha256

from propstore.families.identity.claims import (
    CLAIM_VERSION_ID_EXCLUDED_FIELDS,
    canonicalize_claim_for_version,
)
from propstore.families.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceDocument,
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    """Narrow a decoded JSON value to ``list[object]`` without a cast."""

    return isinstance(value, list)


def _payload(document: msgspec.Struct) -> dict[str, object]:
    """Round-trip a struct into a mutable canonical ``dict[str, object]``."""

    return msgspec.json.decode(msgspec.json.encode(document), type=dict[str, object])


def _hash_payload(payload: object) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: SourceDocument) -> str:
    canonical = _payload(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(justification: SourceJustificationDocument) -> str:
    canonical = _payload(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if _is_object_list(premises):
        canonical["premises"] = sorted(str(premise) for premise in premises)
    return _hash_payload(canonical)


def stance_artifact_code(stance: SourceStanceEntryDocument) -> str:
    canonical = _payload(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def claim_artifact_code(
    claim: SourceClaimDocument,
    *,
    source_code: str,
    justification_codes: Sequence[str],
    stance_codes: Sequence[str],
) -> str:
    canonical = _payload(canonicalize_claim_for_version(claim))
    for field in CLAIM_VERSION_ID_EXCLUDED_FIELDS:
        canonical.pop(field, None)
    canonical.pop("artifact_code", None)
    payload = {
        "source_artifact_code": source_code,
        "claim": canonical,
        "justification_codes": sorted(justification_codes),
        "stance_codes": sorted(stance_codes),
    }
    return _hash_payload(payload)


def stamp_source_artifact_codes(
    source_doc: SourceDocument,
    claims_doc: SourceClaimsDocument | None,
    justifications_doc: SourceJustificationsDocument | None,
    stances_doc: SourceStancesDocument | None,
) -> tuple[
    SourceDocument,
    SourceClaimsDocument | None,
    SourceJustificationsDocument | None,
    SourceStancesDocument | None,
]:
    """Stamp content artifact codes onto a source proposal's artifacts.

    Returns the updated documents (the source manifest, and — when present — the
    claims/justifications/stances containers). Each claim's code folds in the
    source code plus the codes of the justifications concluding it and the stances
    targeting it, so the claim code captures its proposal slice.
    """

    source_code = source_artifact_code(source_doc)
    updated_source = msgspec.structs.replace(source_doc, artifact_code=source_code)

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[SourceJustificationDocument] = []
    for justification in (
        () if justifications_doc is None else justifications_doc.justifications
    ):
        artifact_code = justification_artifact_code(justification)
        rewritten = msgspec.structs.replace(justification, artifact_code=artifact_code)
        conclusion = rewritten.conclusion
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)
    updated_justifications = (
        None
        if justifications_doc is None
        else msgspec.structs.replace(
            justifications_doc, justifications=tuple(rewritten_justifications)
        )
    )

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[SourceStanceEntryDocument] = []
    for stance in () if stances_doc is None else stances_doc.stances:
        artifact_code = stance_artifact_code(stance)
        rewritten = msgspec.structs.replace(stance, artifact_code=artifact_code)
        source_claim = rewritten.source_claim
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)
    updated_stances = (
        None
        if stances_doc is None
        else msgspec.structs.replace(stances_doc, stances=tuple(rewritten_stances))
    )

    rewritten_claims: list[SourceClaimDocument] = []
    for claim in () if claims_doc is None else claims_doc.claims:
        claim_key = "" if claim.artifact_id is None else claim.artifact_id
        artifact_code = claim_artifact_code(
            claim,
            source_code=source_code,
            justification_codes=justification_codes_by_conclusion.get(claim_key, []),
            stance_codes=stance_codes_by_source.get(claim_key, []),
        )
        rewritten_claims.append(
            msgspec.structs.replace(claim, artifact_code=artifact_code)
        )
    updated_claims = (
        None
        if claims_doc is None
        else msgspec.structs.replace(claims_doc, claims=tuple(rewritten_claims))
    )

    return updated_source, updated_claims, updated_justifications, updated_stances

"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Protocol

from quire.hashing import canonical_json_sha256
from quire.documents import convert_document_value

from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceDocument,
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)
from propstore.families.documents.stances import StanceDocument
from propstore.families.identity.claims import canonicalize_claim_for_version


class _PayloadDocument(Protocol):
    def to_payload(self) -> Any: ...


def _payload(document: _PayloadDocument) -> Any:
    return document.to_payload()


def _hash_payload(payload: object) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: SourceDocument) -> str:
    canonical = _payload(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(
    justification: JustificationDocument | SourceJustificationDocument,
) -> str:
    canonical = _payload(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = [
            str(premise)
            for premise in sorted(premises, key=str)
        ]
    return _hash_payload(canonical)


def stance_artifact_code(stance: StanceDocument | SourceStanceEntryDocument) -> str:
    canonical = _payload(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def claim_artifact_code(
    claim: ClaimDocument | SourceClaimDocument,
    *,
    source_code: str,
    justification_codes: Sequence[str],
    stance_codes: Sequence[str],
) -> str:
    canonical = canonicalize_claim_for_version(_payload(claim))
    canonical.pop("artifact_code", None)
    payload = {
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


def _stamp_source_doc(source_doc: SourceDocument, artifact_code: str) -> SourceDocument:
    payload = _payload(source_doc)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        SourceDocument,
        source="artifact-codes:source",
    )


def _stamp_source_claim(claim: SourceClaimDocument, artifact_code: str) -> SourceClaimDocument:
    payload = _payload(claim)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        SourceClaimDocument,
        source="artifact-codes:claim",
    )


def _stamp_source_justification(
    justification: SourceJustificationDocument,
    artifact_code: str,
) -> SourceJustificationDocument:
    payload = _payload(justification)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        SourceJustificationDocument,
        source="artifact-codes:justification",
    )


def _stamp_justification(
    justification: JustificationDocument,
    artifact_code: str,
) -> JustificationDocument:
    payload = _payload(justification)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        JustificationDocument,
        source="artifact-codes:canonical-justification",
    )


def _stamp_source_stance(
    stance: SourceStanceEntryDocument,
    artifact_code: str,
) -> SourceStanceEntryDocument:
    payload = _payload(stance)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        SourceStanceEntryDocument,
        source="artifact-codes:stance",
    )


def _stamp_stance(stance: StanceDocument, artifact_code: str) -> StanceDocument:
    payload = _payload(stance)
    payload["artifact_code"] = artifact_code
    return convert_document_value(
        payload,
        StanceDocument,
        source="artifact-codes:canonical-stance",
    )


def stamp_canonical_artifact_codes(
    source_doc: SourceDocument,
    claims: Sequence[ClaimDocument],
    justifications: Sequence[JustificationDocument],
    stances: Sequence[StanceDocument],
) -> tuple[
    SourceDocument,
    tuple[ClaimDocument, ...],
    tuple[JustificationDocument, ...],
    tuple[StanceDocument, ...],
]:
    source_code = source_artifact_code(source_doc)
    updated_source = _stamp_source_doc(source_doc, source_code)

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[JustificationDocument] = []
    for justification in justifications:
        artifact_code = justification_artifact_code(justification)
        rewritten = _stamp_justification(justification, artifact_code)
        conclusion = rewritten.conclusion
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[StanceDocument] = []
    for stance in stances:
        artifact_code = stance_artifact_code(stance)
        rewritten = _stamp_stance(stance, artifact_code)
        source_claim = rewritten.source_claim
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)

    return (
        updated_source,
        tuple(claims),
        tuple(rewritten_justifications),
        tuple(rewritten_stances),
    )


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
    source_code = source_artifact_code(source_doc)
    updated_source = _stamp_source_doc(source_doc, source_code)

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[SourceJustificationDocument] = []
    for justification in (() if justifications_doc is None else justifications_doc.justifications):
        artifact_code = justification_artifact_code(justification)
        rewritten = _stamp_source_justification(justification, artifact_code)
        conclusion = rewritten.conclusion
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)
    updated_justifications = None
    if justifications_doc is not None:
        justifications_payload = _payload(justifications_doc)
        justifications_payload["justifications"] = [
            justification.to_payload()
            for justification in rewritten_justifications
        ]
        updated_justifications = convert_document_value(
            justifications_payload,
            SourceJustificationsDocument,
            source="artifact-codes:justifications",
        )

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[SourceStanceEntryDocument] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        artifact_code = stance_artifact_code(stance)
        rewritten = _stamp_source_stance(stance, artifact_code)
        source_claim = rewritten.source_claim
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)
    updated_stances = None
    if stances_doc is not None:
        stances_payload = _payload(stances_doc)
        stances_payload["stances"] = [
            stance.to_payload()
            for stance in rewritten_stances
        ]
        updated_stances = convert_document_value(
            stances_payload,
            SourceStancesDocument,
            source="artifact-codes:stances",
        )

    rewritten_claims: list[SourceClaimDocument] = []
    for claim in (() if claims_doc is None else claims_doc.claims):
        claim_id = claim.artifact_id
        justification_codes = justification_codes_by_conclusion.get(str(claim_id), [])
        stance_codes = stance_codes_by_source.get(str(claim_id), [])
        artifact_code = claim_artifact_code(
            claim,
            source_code=source_code,
            justification_codes=justification_codes,
            stance_codes=stance_codes,
        )
        rewritten = _stamp_source_claim(claim, artifact_code)
        rewritten_claims.append(rewritten)
    updated_claims = None
    if claims_doc is not None:
        claims_payload = _payload(claims_doc)
        claims_payload["claims"] = [
            claim.to_payload()
            for claim in rewritten_claims
        ]
        updated_claims = convert_document_value(
            claims_payload,
            SourceClaimsDocument,
            source="artifact-codes:claims",
        )
    return updated_source, updated_claims, updated_justifications, updated_stances

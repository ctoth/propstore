"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from importlib import import_module
from typing import Any, Protocol, TypeAlias

from quire import canonical_json_sha256
from quire.documents import convert_document_value, document_to_payload

from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceJustificationDocument,
    SourceStanceEntryDocument,
)
from propstore.families.documents.stances import StanceDocument
from propstore.families.sources.declaration import SourceDocument, source_document_payload
from propstore.families.identity.claims import canonicalize_claim_for_version

JustificationDocument: TypeAlias = Any


class _PayloadDocument(Protocol):
    def to_payload(self) -> Any: ...


def _justification_document_type() -> type[Any]:
    return getattr(
        import_module("propstore.families.claims.declaration"),
        "JustificationDocument",
    )


def _payload(document: _PayloadDocument | object) -> Any:
    return document_to_payload(document)


def _hash_payload(payload: object) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: SourceDocument) -> str:
    canonical = source_document_payload(source_doc)
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
    payload = source_document_payload(source_doc)
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
        _justification_document_type(),
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
    claims_doc: tuple[SourceClaimDocument, ...] | None,
    justifications_doc: tuple[SourceJustificationDocument, ...] | None,
    stances_doc: tuple[SourceStanceEntryDocument, ...] | None,
) -> tuple[
    SourceDocument,
    tuple[SourceClaimDocument, ...] | None,
    tuple[SourceJustificationDocument, ...] | None,
    tuple[SourceStanceEntryDocument, ...] | None,
]:
    source_code = source_artifact_code(source_doc)
    updated_source = _stamp_source_doc(source_doc, source_code)

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[SourceJustificationDocument] = []
    for justification in (() if justifications_doc is None else justifications_doc):
        artifact_code = justification_artifact_code(justification)
        rewritten = _stamp_source_justification(justification, artifact_code)
        conclusion = rewritten.conclusion
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)
    updated_justifications = None
    if justifications_doc is not None:
        updated_justifications = tuple(rewritten_justifications)

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[SourceStanceEntryDocument] = []
    for stance in (() if stances_doc is None else stances_doc):
        artifact_code = stance_artifact_code(stance)
        rewritten = _stamp_source_stance(stance, artifact_code)
        source_claim = rewritten.source_claim
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)
    updated_stances = None
    if stances_doc is not None:
        updated_stances = tuple(rewritten_stances)

    rewritten_claims: list[SourceClaimDocument] = []
    for claim in (() if claims_doc is None else claims_doc):
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
        updated_claims = tuple(rewritten_claims)
    return updated_source, updated_claims, updated_justifications, updated_stances

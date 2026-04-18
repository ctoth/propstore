from __future__ import annotations

import hashlib
import json
from pathlib import Path

from propstore.artifacts import SOURCE_CLAIMS_FAMILY, SourceRef
from propstore.artifacts.documents.claims import ClaimLogicalIdDocument, ClaimSourceDocument
from propstore.core.claim_types import ClaimType, coerce_claim_type
from propstore.artifacts.documents.sources import SourceProvenanceDocument
from propstore.repository import Repository
from propstore.artifacts.schema import convert_document_value, decode_document_path
from propstore.identity import (
    compute_claim_version_id,
    derive_claim_artifact_id,
    normalize_logical_value,
)

from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    normalize_source_slug,
    source_branch_name,
    source_tag_uri,
)
from propstore.artifacts.documents.sources import ExtractionProvenanceDocument, SourceClaimDocument, SourceClaimsDocument


def stable_claim_logical_value(claim: SourceClaimDocument, *, source_uri: str) -> str:
    canonical = claim.to_payload()
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
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"claim_{digest}"


def source_concept_handles(repo: Repository, source_name: str) -> set[str]:
    handles: set[str] = set()
    concepts_doc = load_source_concepts_document(repo, source_name)
    if concepts_doc is None:
        return handles
    for entry in concepts_doc.concepts:
        if entry.local_name:
            handles.add(entry.local_name)
        if entry.proposed_name:
            handles.add(entry.proposed_name)
    return handles


def iter_claim_concept_refs(claim: SourceClaimDocument) -> list[str]:
    refs: list[str] = []
    for value in (claim.concept, claim.target_concept):
        if isinstance(value, str):
            refs.append(value)
    refs.extend(claim.concepts)
    variables = claim.variables
    if isinstance(variables, tuple):
        refs.extend(variable.concept for variable in variables if isinstance(variable.concept, str))
    parameters = claim.parameters
    refs.extend(parameter.concept for parameter in parameters if isinstance(parameter.concept, str))
    return refs


def validate_source_claim_concepts(repo: Repository, source_name: str, data: SourceClaimsDocument) -> None:
    known_handles = source_concept_handles(repo, source_name)
    unknown: set[str] = set()
    for claim in data.claims:
        for concept_ref in iter_claim_concept_refs(claim):
            if concept_ref.startswith("ps:concept:") or concept_ref.startswith("tag:"):
                continue
            if concept_ref not in known_handles:
                unknown.add(concept_ref)
    if unknown:
        formatted = ", ".join(sorted(unknown))
        raise ValueError(f"unknown concept reference(s): {formatted}")


def normalize_source_claims_payload(
    data: SourceClaimsDocument,
    *,
    source_uri: str,
    source_namespace: str,
) -> tuple[SourceClaimsDocument, dict[str, str]]:
    normalized_claims: list[SourceClaimDocument] = []
    local_to_canonical: dict[str, str] = {}
    namespace = normalize_source_slug(source_namespace)

    for index, claim in enumerate(data.claims, start=1):
        normalized = claim.to_payload()
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
                logical_ids.append(ClaimLogicalIdDocument(namespace=namespace, value=local_value))
        else:
            normalized.pop("source_local_id", None)
        normalized["logical_ids"] = logical_ids
        normalized["artifact_id"] = derive_claim_artifact_id(namespace, stable_value)
        normalized["version_id"] = compute_claim_version_id(
            {
                **normalized,
                "logical_ids": [logical_id.to_payload() for logical_id in logical_ids],
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
        SourceClaimsDocument(
            source=data.source,
            claims=tuple(normalized_claims),
            produced_by=data.produced_by,
        ),
        local_to_canonical,
    )


def commit_source_claims_batch(
    repo: Repository,
    source_name: str,
    claims_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
) -> str:
    from datetime import datetime

    source_doc = load_source_document(repo, source_name)
    raw = decode_document_path(claims_file, SourceClaimsDocument)
    if reader is not None:
        raw = SourceClaimsDocument(
            source=raw.source,
            claims=raw.claims,
            produced_by=ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
    validate_source_claim_concepts(repo, source_name, raw)
    normalized, _ = normalize_source_claims_payload(
        raw,
        source_uri=source_doc.id or source_tag_uri(repo, source_name),
        source_namespace=normalize_source_slug(source_name),
    )
    return repo.artifacts.save(
        SOURCE_CLAIMS_FAMILY,
        SourceRef(source_name),
        normalized,
        message=f"Write claims for {normalize_source_slug(source_name)}",
    )


def commit_source_claim_proposal(
    repo: Repository,
    source_name: str,
    *,
    claim_id: str,
    claim_type: ClaimType,
    statement: str | None = None,
    concept: str | None = None,
    value: float | None = None,
    unit: str | None = None,
    context: str,
    page: int | None = None,
) -> SourceClaimDocument:
    branch = source_branch_name(source_name)
    source_doc = load_source_document(repo, source_name)
    existing = load_source_claims_document(repo, source_name) or SourceClaimsDocument(
        source=ClaimSourceDocument(paper=normalize_source_slug(source_name)),
        claims=(),
    )
    claims = list(existing.claims)

    norm_keys = {"source_local_id", "logical_ids", "artifact_id", "version_id"}
    restored: list[SourceClaimDocument] = []
    for claim in claims:
        if claim.source_local_id == claim_id or claim.id == claim_id:
            continue
        restored_claim = {key: value for key, value in claim.to_payload().items() if key not in norm_keys}
        local_id = claim.source_local_id
        if local_id:
            restored_claim["id"] = local_id
        restored.append(
            convert_document_value(
                restored_claim,
                SourceClaimDocument,
                source=f"{branch}:claims proposal {claim_id}",
            )
        )
    claims = restored

    normalized_claim_type = coerce_claim_type(claim_type)
    assert normalized_claim_type is not None

    claim_payload: dict[str, object] = {
        "id": claim_id,
        "type": normalized_claim_type.value,
        "context": context,
    }
    if statement is not None:
        claim_payload["statement"] = statement
    if concept is not None:
        claim_payload["concept"] = concept
    if value is not None:
        claim_payload["value"] = value
    if unit is not None:
        claim_payload["unit"] = unit
    if page is not None:
        claim_payload["provenance"] = SourceProvenanceDocument(
            paper=normalize_source_slug(source_name),
            page=page,
        )

    claims.append(
        convert_document_value(
            claim_payload,
            SourceClaimDocument,
            source=f"{branch}:claims proposal {claim_id}",
        )
    )
    data = SourceClaimsDocument(
        source=existing.source or ClaimSourceDocument(paper=normalize_source_slug(source_name)),
        claims=tuple(claims),
    )

    normalized, _ = normalize_source_claims_payload(
        data,
        source_uri=source_doc.id or source_tag_uri(repo, source_name),
        source_namespace=normalize_source_slug(source_name),
    )

    repo.artifacts.save(
        SOURCE_CLAIMS_FAMILY,
        SourceRef(source_name),
        normalized,
        message=f"Propose claim for {normalize_source_slug(source_name)}",
    )

    for entry in normalized.claims:
        if entry.source_local_id == claim_id:
            return entry
    return normalized.claims[-1]

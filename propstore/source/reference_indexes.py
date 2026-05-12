from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quire.references import FamilyReferenceIndex, ReferenceKey

from propstore.families.documents.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.families.registry import SourceRef

if TYPE_CHECKING:
    from propstore.families.claims.documents import ClaimDocument
    from propstore.repository import Repository


SOURCE_CLAIM_REFERENCE_KEYS = (
    ReferenceKey.field("source_local_id"),
    ReferenceKey.field("logical_ids[].formatted"),
    ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
)


@dataclass(frozen=True)
class ImportedClaimHandle:
    handle: str
    artifact_id: str


def source_claim_index_from_document(
    document: SourceClaimsDocument | None,
) -> FamilyReferenceIndex[SourceClaimDocument]:
    records = () if document is None else document.claims
    return FamilyReferenceIndex.from_records(
        records,
        family="source_claims",
        artifact_id=lambda claim: claim.artifact_id,
        keys=SOURCE_CLAIM_REFERENCE_KEYS,
    )


def source_claim_index(repo: Repository, source_name: str) -> FamilyReferenceIndex[SourceClaimDocument]:
    document = repo.families.source_claims.load(SourceRef(source_name))
    return source_claim_index_from_document(document)


def primary_claim_index(repo: Repository) -> FamilyReferenceIndex[ClaimDocument]:
    return repo.families.claims.reference_index()


def imported_claim_handle_index(
    handles: Iterable[ImportedClaimHandle],
) -> FamilyReferenceIndex[ImportedClaimHandle]:
    return FamilyReferenceIndex.from_records(
        handles,
        family="imported_claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(lambda handle: (handle.handle,),),
    )


def resolve_source_or_primary_claim_id(
    reference: object,
    *,
    source: FamilyReferenceIndex[Any],
    primary: FamilyReferenceIndex[Any] | None = None,
) -> str | None:
    resolved = source.resolve_id(reference)
    if resolved is not None:
        return resolved
    if primary is None:
        return None
    return primary.resolve_id(reference)

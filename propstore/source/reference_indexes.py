from __future__ import annotations

from typing import TYPE_CHECKING

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

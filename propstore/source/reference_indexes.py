from __future__ import annotations

from typing import TYPE_CHECKING

from quire.references import FamilyReferenceIndex

from propstore.families.claims.declaration import SourceClaimDocument
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PropstoreFamily,
    SourceRef,
)

if TYPE_CHECKING:
    from propstore.families.claims.declaration import ClaimDocument
    from propstore.repository import Repository


def source_claim_index(
    repo: Repository, source_name: str
) -> FamilyReferenceIndex[SourceClaimDocument]:
    document = repo.families.source_claims.load(SourceRef(source_name))
    family = PROPSTORE_FAMILY_REGISTRY.by_key(PropstoreFamily.SOURCE_CLAIMS)
    return family.reference_index_from_records(() if document is None else document)


def primary_claim_index(repo: Repository) -> FamilyReferenceIndex[ClaimDocument]:
    return repo.families.claims.reference_index()

"""Reference lowering for source-branch claims.

The source-local handle a claim is authored with (``source_local_id``, or a
``namespace:value`` logical id) is resolved to its canonical claim artifact id
through quire's :class:`~quire.references.FamilyReferenceIndex` — never by string
munging. This is the read side of the boundary CLAUDE.md names: "source-local
handles are lowered explicitly inside the source subsystem before canonical
writes." :func:`resolve_source_or_primary_claim_id` resolves against the source
branch's own claims first, then the primary (canonical) claim index.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from quire.references import FamilyReferenceIndex, ReferenceKey

from propstore.families.claims import Claim
from propstore.families.registry import SourceRef
from propstore.families.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.repository import Repository

SOURCE_CLAIM_REFERENCE_KEYS = (
    ReferenceKey.field("source_local_id"),
    ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
)


@dataclass(frozen=True)
class ImportedClaimHandle:
    """A claim handle observed during import, paired with its artifact id."""

    handle: str
    artifact_id: str


def source_claim_index_from_document(
    document: SourceClaimsDocument | None,
) -> FamilyReferenceIndex[SourceClaimDocument]:
    """Build a reference index over a source branch's claim documents."""

    records: tuple[SourceClaimDocument, ...] = () if document is None else document.claims
    return FamilyReferenceIndex[SourceClaimDocument].from_records(
        records,
        family="source_claims",
        artifact_id=lambda claim: claim.artifact_id,
        keys=SOURCE_CLAIM_REFERENCE_KEYS,
    )


def source_claim_index(
    repo: Repository, source_name: str
) -> FamilyReferenceIndex[SourceClaimDocument]:
    """Build a reference index over the named source branch's claims."""

    document = repo.families.source_claims.load(SourceRef(source_name))
    typed = document if isinstance(document, SourceClaimsDocument) else None
    return source_claim_index_from_document(typed)


def primary_claim_index(repo: Repository) -> FamilyReferenceIndex[Claim]:
    """Build a reference index over the primary-branch canonical claims."""

    index: FamilyReferenceIndex[Claim] = repo.families.claim.reference_index()
    return index


def imported_claim_handle_index(
    handles: Iterable[ImportedClaimHandle],
) -> FamilyReferenceIndex[ImportedClaimHandle]:
    """Build a reference index resolving an imported handle to its artifact id."""

    def handle_reference_keys(record: ImportedClaimHandle) -> tuple[str, ...]:
        return (record.handle,)

    return FamilyReferenceIndex[ImportedClaimHandle].from_records(
        handles,
        family="imported_claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(handle_reference_keys,),
    )


def resolve_source_or_primary_claim_id(
    reference: object,
    *,
    source: FamilyReferenceIndex[SourceClaimDocument],
    primary: FamilyReferenceIndex[Claim] | None = None,
) -> str | None:
    """Resolve *reference* against the source index, falling back to primary."""

    resolved = source.resolve_id(reference)
    if resolved is not None:
        return resolved
    if primary is None:
        return None
    return primary.resolve_id(reference)

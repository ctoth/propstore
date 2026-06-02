"""Quire reference indexes for claim family records."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from quire.documents import LoadedDocument
from quire.references import FamilyReferenceIndex

from propstore.families.claims.declaration import (
    ClaimDocument,
    claim_logical_id_formatted,
)
from propstore.families.identity.claims import derive_claim_artifact_id
from propstore.families.identity.logical_ids import (
    normalize_identity_namespace,
    normalize_logical_value,
)


@dataclass(frozen=True)
class ClaimReferenceRecord:
    claim: ClaimDocument
    source_paper: str

    @property
    def artifact_id(self) -> str | None:
        if isinstance(self.claim.artifact_id, str) and self.claim.artifact_id:
            return self.claim.artifact_id
        raw_id = self.claim.id
        if isinstance(raw_id, str) and raw_id:
            return derive_claim_artifact_id(
                self.source_paper,
                normalize_logical_value(raw_id),
            )
        return None


@dataclass(frozen=True)
class ImportedClaimReference:
    handle: str
    artifact_id: str


def claim_reference_keys(record: ClaimReferenceRecord) -> tuple[str, ...]:
    keys: list[str] = []
    raw_id = record.claim.id
    if isinstance(raw_id, str) and raw_id:
        keys.append(raw_id)
        keys.append(
            f"{normalize_identity_namespace(record.source_paper)}:"
            f"{normalize_logical_value(raw_id)}"
        )
    for logical_id in record.claim.logical_ids:
        keys.append(claim_logical_id_formatted(logical_id))
        keys.append(logical_id.value)
    return tuple(keys)


def claim_reference_records(
    claims: Sequence[LoadedDocument[ClaimDocument]],
) -> tuple[ClaimReferenceRecord, ...]:
    records: list[ClaimReferenceRecord] = []
    for loaded in claims:
        source = loaded.document.source
        provenance = loaded.document.provenance
        source_paper = (
            source.paper
            if source is not None
            else (
                provenance.paper
                if provenance is not None and provenance.paper is not None
                else loaded.filename
            )
        )
        records.append(
            ClaimReferenceRecord(
                claim=loaded.document,
                source_paper=str(source_paper),
            )
        )
    return tuple(records)


def build_claim_reference_index(
    claims: Sequence[LoadedDocument[ClaimDocument]],
) -> FamilyReferenceIndex[ClaimReferenceRecord]:
    return FamilyReferenceIndex.from_records(
        claim_reference_records(claims),
        family="claim",
        artifact_id=lambda record: record.artifact_id,
        keys=(claim_reference_keys,),
    )


def imported_claim_reference_index(
    handles: Iterable[ImportedClaimReference],
) -> FamilyReferenceIndex[ImportedClaimReference]:
    def reference_keys(record: ImportedClaimReference) -> tuple[str]:
        return (record.handle,)

    return FamilyReferenceIndex.from_records(
        handles,
        family="imported_claims",
        artifact_id=lambda handle: handle.artifact_id,
        keys=(reference_keys,),
    )


def resolve_first_claim_reference_id(
    reference: object,
    *indexes: FamilyReferenceIndex[Any] | None,
) -> str | None:
    for index in indexes:
        if index is None:
            continue
        resolved = index.resolve_id(reference)
        if resolved is not None:
            return resolved
    return None

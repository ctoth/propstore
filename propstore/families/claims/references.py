"""Quire reference indexes for claim family records."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quire.references import FamilyReferenceIndex

from propstore.claims import (
    ClaimFileEntry,
    claim_file_claims,
    claim_file_filename,
    claim_file_source_paper,
)
from propstore.families.claims.documents import ClaimDocument
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
        keys.append(logical_id.formatted)
        keys.append(logical_id.value)
    return tuple(keys)


def claim_reference_records(
    claim_files: Sequence[ClaimFileEntry],
) -> tuple[ClaimReferenceRecord, ...]:
    records: list[ClaimReferenceRecord] = []
    for claim_file in claim_files:
        source_paper = claim_file_source_paper(claim_file) or claim_file_filename(claim_file)
        records.extend(
            ClaimReferenceRecord(claim=claim, source_paper=str(source_paper))
            for claim in claim_file_claims(claim_file)
        )
    return tuple(records)


def build_claim_file_reference_index(
    claim_files: Sequence[ClaimFileEntry],
) -> FamilyReferenceIndex[ClaimReferenceRecord]:
    return FamilyReferenceIndex.from_records(
        claim_reference_records(claim_files),
        family="claim",
        artifact_id=lambda record: record.artifact_id,
        keys=(claim_reference_keys,),
    )

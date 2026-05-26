from __future__ import annotations

from typing import Any, cast

from quire.documents import convert_document_value, document_to_payload
from quire.references import FamilyReferenceIndex

from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.documents.sources import SourceClaimDocument, SourceStanceEntryDocument


def normalize_source_stances_payload(
    data: tuple[SourceStanceEntryDocument, ...],
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Any] | None = None,
) -> tuple[SourceStanceEntryDocument, ...]:
    normalized_stances: list[SourceStanceEntryDocument] = []
    for index, stance in enumerate(data, start=1):
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        normalized = cast(dict[str, Any], document_to_payload(stance))
        normalized["source_claim"] = claim_index.require_id(stance.source_claim)
        target = resolve_first_claim_reference_id(
            stance.target,
            claim_index,
            primary_claim_index,
        )
        if target is None:
            raise ValueError(f"unresolved stance target: {stance.target}")
        normalized["target"] = target
        normalized_stances.append(
            convert_document_value(
                normalized,
                SourceStanceEntryDocument,
                source=f"stances[{index}]",
            )
        )
    return tuple(normalized_stances)

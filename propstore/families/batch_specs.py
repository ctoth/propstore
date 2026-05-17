from __future__ import annotations

from quire.documents import DocumentBatchSpec

from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceConceptEntryDocument,
    SourceJustificationDocument,
    SourceStanceEntryDocument,
)

CLAIM_BATCH_SPEC = DocumentBatchSpec(
    batch_name="claims",
    item_type=ClaimDocument,
    items_field="claims",
    inherited_item_fields=("source",),
)

SOURCE_CONCEPT_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-concepts",
    item_type=SourceConceptEntryDocument,
    items_field="concepts",
)

SOURCE_CLAIM_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-claims",
    item_type=SourceClaimDocument,
    items_field="claims",
    inherited_item_fields=("source", "produced_by"),
)

SOURCE_JUSTIFICATION_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-justifications",
    item_type=SourceJustificationDocument,
    items_field="justifications",
    inherited_item_fields=("source",),
)

SOURCE_STANCE_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-stances",
    item_type=SourceStanceEntryDocument,
    items_field="stances",
    inherited_item_fields=("source",),
)

SOURCE_MICROPUBLICATION_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-micropublications",
    item_type=MicropublicationDocument,
    items_field="micropublications",
    inherited_item_fields=("source",),
)

__all__ = [
    "CLAIM_BATCH_SPEC",
    "SOURCE_CLAIM_BATCH_SPEC",
    "SOURCE_CONCEPT_BATCH_SPEC",
    "SOURCE_JUSTIFICATION_BATCH_SPEC",
    "SOURCE_MICROPUBLICATION_BATCH_SPEC",
    "SOURCE_STANCE_BATCH_SPEC",
]

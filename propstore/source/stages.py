"""Source-family semantic stage objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeAlias

from propstore.families.claims.documents import ClaimDocument
from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.micropublications.declaration import MicropublicationDocument
from propstore.families.documents.sources import (
    SourceClaimDocument,
)
from propstore.families.stances.declaration import StanceDocument
from propstore.families.sources.declaration import SourceDocument
from propstore.families.registry import (
    CanonicalSourceRef,
    ClaimRef,
    ConceptFileRef,
    JustificationRef,
    MicropublicationRef,
    StanceRef,
)

JustificationDocument: TypeAlias = Any

@dataclass(frozen=True)
class SourcePromotionPlan:
    source_name: str
    slug: str
    source_branch: str
    source_ref: CanonicalSourceRef
    promoted_source_document: SourceDocument
    promoted_claim_documents: dict[ClaimRef, ClaimDocument] = field(
        default_factory=dict
    )
    promoted_micropub_documents: dict[MicropublicationRef, MicropublicationDocument] = field(
        default_factory=dict
    )
    promoted_concept_documents: dict[ConceptFileRef, ConceptDocument] = field(
        default_factory=dict
    )
    promoted_justification_documents: dict[JustificationRef, JustificationDocument] = field(
        default_factory=dict
    )
    promoted_stance_documents: dict[StanceRef, StanceDocument] = field(
        default_factory=dict
    )
    blocked_claims: tuple[SourceClaimDocument, ...] = ()
    blocked_reasons: dict[str, list[tuple[str, str]]] = field(default_factory=dict)

"""Source-family semantic stage objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from quire.artifacts import ArtifactFamily
from quire.family_store import DocumentFamilyStore

from propstore.families.addresses import SemanticFamilyAddress
from propstore.claim_references import ImportedClaimHandleIndex
from propstore.families.claims.documents import ClaimsFileDocument
from propstore.families.concepts.documents import ConceptDocument
from propstore.families.documents.micropubs import MicropublicationsFileDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceDocument,
)
from propstore.families.documents.stances import StanceDocument
from propstore.families.registry import (
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptFileRef,
    JustificationRef,
    MicropubsFileRef,
    StanceRef,
)


class SourceStage(StrEnum):
    IMPORT_AUTHORED = "source.import_authored"
    IMPORT_NORMALIZED = "source.import_normalized"


@dataclass(frozen=True)
class PlannedSemanticWrite:
    family: ArtifactFamily[Any, Any, Any]
    ref: object
    document: object
    relpath: SemanticFamilyAddress


@dataclass(frozen=True)
class SourceImportAuthoredWrites:
    store: DocumentFamilyStore[Any]
    writes: Mapping[str, bytes]
    repository_name: str


@dataclass(frozen=True)
class SourceImportNormalizedWrites:
    writes: dict[str, PlannedSemanticWrite]
    warnings: tuple[str, ...] = ()


@dataclass
class SourceImportState:
    repository_name: str
    concept_ref_map: dict[str, str] = field(default_factory=dict)
    local_handle_index: ImportedClaimHandleIndex = field(
        default_factory=ImportedClaimHandleIndex
    )
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourcePromotionPlan:
    source_name: str
    slug: str
    source_branch: str
    source_ref: CanonicalSourceRef
    claims_ref: ClaimsFileRef
    promoted_source_document: SourceDocument
    promoted_claims_document: ClaimsFileDocument
    promoted_micropubs_ref: MicropubsFileRef | None = None
    promoted_micropubs_document: MicropublicationsFileDocument | None = None
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

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

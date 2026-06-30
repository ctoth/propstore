"""Typed plan objects for the source semantic pipeline.

These are pure data carriers (no behaviour) describing planned semantic writes
during source import. ``SourcePromotionPlan`` — which carries the *canonical*
claim/concept/micropub/justification/stance documents a promotion produces — is
deferred to the promote subsystem (Phase 8-3), where those canonical charters
land; building it here would require mirroring charters that do not yet exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from quire.artifacts import ArtifactFamily
from quire.family_store import DocumentFamilyStore

from propstore.source.reference_indexes import ImportedClaimHandle


def _empty_str_map() -> dict[str, str]:
    return {}


def _empty_handle_list() -> list[ImportedClaimHandle]:
    return []


def _empty_str_list() -> list[str]:
    return []


class SourceStage(StrEnum):
    IMPORT_AUTHORED = "source.import_authored"
    IMPORT_NORMALIZED = "source.import_normalized"


@dataclass(frozen=True)
class PlannedSemanticWrite:
    """One planned write into a semantic family during import."""

    family: ArtifactFamily[object, object, object]
    ref: object
    document: object
    relpath: str


@dataclass(frozen=True)
class SourceImportAuthoredWrites:
    """The raw authored byte-writes captured from a source branch."""

    store: DocumentFamilyStore[object]
    writes: Mapping[str, bytes]
    repository_name: str


@dataclass(frozen=True)
class SourceImportNormalizedWrites:
    """The normalized semantic writes plus any non-fatal ambiguity warnings."""

    writes: dict[str, PlannedSemanticWrite]
    warnings: tuple[str, ...] = ()


@dataclass
class SourceImportState:
    """Mutable accumulator threaded through the import normalization passes."""

    repository_name: str
    concept_ref_map: dict[str, str] = field(default_factory=_empty_str_map)
    imported_claim_handles: list[ImportedClaimHandle] = field(
        default_factory=_empty_handle_list
    )
    warnings: list[str] = field(default_factory=_empty_str_list)

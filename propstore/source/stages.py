"""Typed plan objects for the source semantic pipeline.

These are pure data carriers (no behaviour) describing planned semantic writes
during source import, plus :class:`SourcePromotionPlan` — the canonical
claim/concept/micropub/justification/stance charters a promotion will commit,
assembled before the atomic master write so the write is a pure replay.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from quire.artifacts import ArtifactFamily
from quire.family_store import DocumentFamilyStore

from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance
from propstore.families.sources import SourceClaimDocument
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


@dataclass(frozen=True)
class AlignRepositorySnapshotsRequest:
    """Explicit import branches to pin and align as committed KB snapshots."""

    import_branches: tuple[str, ...]


@dataclass(frozen=True)
class SourcePromotionPlan:
    """The canonical charters a source promotion will commit to ``master``.

    Assembled (and validated) before the atomic head-bound transaction so the
    commit itself is a pure replay of these maps. ``blocked_claims`` /
    ``blocked_reasons`` carry the per-item quarantine: claims that could not be
    promoted cleanly are recorded here, stay on the source branch, and are
    surfaced — never dropped (the non-commitment discipline).
    """

    source_name: str
    slug: str
    source_branch: str
    promoted_concept_documents: dict[str, Concept]
    promoted_claim_documents: dict[str, Claim]
    promoted_micropub_documents: dict[str, Micropublication]
    promoted_justification_documents: dict[str, Justification]
    promoted_stance_documents: dict[str, Stance]
    blocked_claims: tuple[SourceClaimDocument, ...]
    blocked_reasons: dict[str, tuple[tuple[str, str], ...]]


@dataclass
class SourceImportState:
    """Mutable accumulator threaded through the import normalization passes."""

    repository_name: str
    concept_ref_map: dict[str, str] = field(default_factory=_empty_str_map)
    imported_claim_handles: list[ImportedClaimHandle] = field(
        default_factory=_empty_handle_list
    )
    warnings: list[str] = field(default_factory=_empty_str_list)

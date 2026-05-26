"""Source-family semantic stage objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from quire.lifecycle import FamilyRecordWrite

from propstore.families.documents.sources import SourceClaimDocument


@dataclass(frozen=True)
class SourcePromotionPlan:
    source_name: str
    slug: str
    source_branch: str
    writes: tuple[FamilyRecordWrite, ...] = ()
    blocked_claims: tuple[SourceClaimDocument, ...] = ()
    blocked_reasons: dict[str, list[tuple[str, str]]] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceFinalizePlan:
    source_name: str
    source_branch: str
    writes: tuple[FamilyRecordWrite, ...] = ()

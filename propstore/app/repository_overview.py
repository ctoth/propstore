"""Application-layer repository-overview report for the `/`-index page.

Holds typed dataclass shapes only at this step. The composition function
`build_repository_overview` is added in a later TDD step.

Honest-vacuous discipline: every aggregate section carries an explicit
`state` field whose values are constrained to `OverviewState`. Sections
that the system cannot yet answer report `state="not_implemented"` with
an explanatory sentence rather than fabricating data or silently
omitting the row.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from propstore.app.rendering import AppRenderPolicyRequest, RenderPolicySummary
from propstore.app.repository_views import AppRepositoryViewRequest


OverviewState: TypeAlias = Literal["known", "vacuous", "not_implemented"]


@dataclass(frozen=True)
class RepositoryOverviewRequest:
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)
    repository_view: AppRepositoryViewRequest = field(default_factory=AppRepositoryViewRequest)


@dataclass(frozen=True)
class InventoryRow:
    kind: str
    count: int
    state: OverviewState
    sentence: str
    href: str | None


@dataclass(frozen=True)
class SourcePointer:
    state: OverviewState
    source_id: str | None
    slug: str | None
    kind: str | None
    sentence: str
    href: str | None


@dataclass(frozen=True)
class ProvenanceStateCount:
    state: str
    count: int


@dataclass(frozen=True)
class ProvenanceSummary:
    state: OverviewState
    counts: tuple[ProvenanceStateCount, ...]
    sentence: str


@dataclass(frozen=True)
class RecentActivityEntry:
    when: str
    what: str
    href: str | None


@dataclass(frozen=True)
class RecentActivity:
    state: OverviewState
    entries: tuple[RecentActivityEntry, ...]
    sentence: str


@dataclass(frozen=True)
class NotableConflictPointer:
    claim_id: str
    sentence: str
    href: str | None


@dataclass(frozen=True)
class NotableConflicts:
    state: OverviewState
    entries: tuple[NotableConflictPointer, ...]
    sentence: str


@dataclass(frozen=True)
class RepositoryOverviewReport:
    repository_state: str
    render_policy: RenderPolicySummary
    inventory_rows: tuple[InventoryRow, ...]
    source_pointers: tuple[SourcePointer, ...]
    provenance_summary: ProvenanceSummary
    recent_activity: RecentActivity
    notable_conflicts: NotableConflicts
    prose_summary: str

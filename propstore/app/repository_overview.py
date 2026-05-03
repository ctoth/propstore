"""Application-layer repository-overview report for the `/`-index page.

Honest-vacuous discipline: every aggregate section carries an explicit
`state` field constrained to `OverviewState`. Sections that the system
cannot yet answer report `state="not_implemented"` with an explanatory
sentence rather than fabricating data or silently omitting the row.

Inventory composition is driven by `KIND_REGISTRY`: a tuple of
`KindContributor`. Each contributor names a kind, its canonical web
href, a counter callable, and the sidecar-missing exception types that
should lower the row to `state="vacuous"` rather than crash the whole
report. The renderer iterates `inventory_rows`; it never enumerates
kind names.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from propstore.app.claim_views import ClaimListRequest, list_claim_views
from propstore.app.concepts import (
    ConceptListRequest,
    ConceptSidecarMissingError,
    list_concepts,
)
from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicySummary,
    build_render_policy,
    summarize_render_policy,
)
from propstore.app.repository_history import (
    BranchNotFoundError,
    LogRecord,
    build_log_report,
)
from propstore.app.repository_views import (
    AppRepositoryViewRequest,
    repository_view_label,
)
from propstore.app.sources import SourceListItem, list_sources
from propstore.app.world import WorldSidecarMissingError
from propstore.repository import Repository


OverviewState: TypeAlias = Literal["known", "vacuous", "not_implemented"]

_INVENTORY_PROBE_LIMIT = 10_000
"""Upper bound passed to underlying ``list_*`` calls when building the
inventory count. Existing ``list_*`` surfaces paginate; we send a high
limit and report what came back. A future unbounded ``count_*`` surface
will replace this; tracked in ``docs/gaps.md``.
"""

_RECENT_ACTIVITY_COUNT = 10
"""Upper bound on log entries projected into ``RecentActivity.entries``."""

_RECENT_ACTIVITY_MESSAGE_TRUNCATE = 80
"""Maximum message length carried in ``RecentActivityEntry.what``."""


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


@dataclass(frozen=True)
class KindContributor:
    kind: str
    href: str | None
    count: Callable[[Repository], int]
    sidecar_missing: tuple[type[Exception], ...]


def _count_claims(repo: Repository) -> int:
    request = ClaimListRequest(limit=_INVENTORY_PROBE_LIMIT)
    return len(list_claim_views(repo, request).entries)


def _count_concepts(repo: Repository) -> int:
    request = ConceptListRequest(limit=_INVENTORY_PROBE_LIMIT)
    return len(list_concepts(repo, request).entries)


KIND_REGISTRY: tuple[KindContributor, ...] = (
    KindContributor(
        kind="claims",
        href="/claims",
        count=_count_claims,
        sidecar_missing=(WorldSidecarMissingError,),
    ),
    KindContributor(
        kind="concepts",
        href="/concepts",
        count=_count_concepts,
        sidecar_missing=(ConceptSidecarMissingError,),
    ),
)


def build_repository_overview(
    repo: Repository,
    request: RepositoryOverviewRequest,
) -> RepositoryOverviewReport:
    repository_state = repository_view_label(request.repository_view)
    policy = summarize_render_policy(build_render_policy(request.render_policy))
    inventory_rows = tuple(_build_inventory_row(repo, kc) for kc in KIND_REGISTRY)

    return RepositoryOverviewReport(
        repository_state=repository_state,
        render_policy=policy,
        inventory_rows=inventory_rows,
        source_pointers=_build_source_pointers(repo),
        provenance_summary=ProvenanceSummary(
            state="not_implemented",
            counts=(),
            sentence="Provenance aggregation is not yet computed.",
        ),
        recent_activity=_build_recent_activity(repo),
        notable_conflicts=NotableConflicts(
            state="not_implemented",
            entries=(),
            sentence="Notable conflicts are not yet computed.",
        ),
        prose_summary=_compose_prose_summary(
            repository_state, inventory_rows, policy
        ),
    )


def _compose_prose_summary(
    repository_state: str,
    inventory_rows: tuple[InventoryRow, ...],
    policy: RenderPolicySummary,
) -> str:
    known_rows = tuple(row for row in inventory_rows if row.state == "known")
    total = sum(row.count for row in known_rows)
    if not inventory_rows:
        return (
            f"Repository at {repository_state}; no inventory kinds registered "
            f"under {policy.semantics} semantics."
        )
    if not known_rows:
        return (
            f"Repository at {repository_state}; 0 indexed entries visible across "
            f"{len(inventory_rows)} inventory kinds (sidecar unavailable) under "
            f"{policy.semantics} semantics."
        )
    return (
        f"Repository at {repository_state}; {total} indexed entries across "
        f"{len(known_rows)} of {len(inventory_rows)} inventory kinds under "
        f"{policy.semantics} semantics."
    )


def _build_recent_activity(repo: Repository) -> RecentActivity:
    try:
        log_report = build_log_report(
            repo,
            count=_RECENT_ACTIVITY_COUNT,
            branch_name=None,
            show_files=False,
        )
    except BranchNotFoundError as exc:
        return RecentActivity(
            state="vacuous",
            entries=(),
            sentence=f"Recent activity unavailable: {exc!s}.",
        )
    if not log_report.entries:
        return RecentActivity(
            state="vacuous",
            entries=(),
            sentence="No commits on the current branch yet.",
        )
    return RecentActivity(
        state="known",
        entries=tuple(_recent_entry_from_log(record) for record in log_report.entries),
        sentence=(
            f"Last {len(log_report.entries)} commits on {log_report.branch}."
        ),
    )


def _recent_entry_from_log(record: LogRecord) -> RecentActivityEntry:
    message = record.message
    if len(message) > _RECENT_ACTIVITY_MESSAGE_TRUNCATE:
        message = message[: _RECENT_ACTIVITY_MESSAGE_TRUNCATE - 1] + "…"
    return RecentActivityEntry(
        when=record.time,
        what=f"{record.operation}: {message}",
        href=None,
    )


def _build_source_pointers(repo: Repository) -> tuple[SourcePointer, ...]:
    report = list_sources(repo)
    return tuple(_source_pointer_from_item(item) for item in report.items)


def _source_pointer_from_item(item: SourceListItem) -> SourcePointer:
    return SourcePointer(
        state="known",
        source_id=item.name,
        slug=item.name,
        kind="source",
        sentence=f"Source {item.name} on branch {item.branch} at {item.tip_sha[:8]}.",
        href=None,
    )


def _build_inventory_row(
    repo: Repository,
    contributor: KindContributor,
) -> InventoryRow:
    if contributor.sidecar_missing:
        try:
            count = contributor.count(repo)
        except contributor.sidecar_missing as exc:
            return InventoryRow(
                kind=contributor.kind,
                count=0,
                state="vacuous",
                sentence=f"{contributor.kind}: sidecar unavailable ({exc!s}).",
                href=contributor.href,
            )
    else:
        count = contributor.count(repo)
    return InventoryRow(
        kind=contributor.kind,
        count=count,
        state="known",
        sentence=f"{count} {contributor.kind} present (probe limit {_INVENTORY_PROBE_LIMIT}).",
        href=contributor.href,
    )

"""Application-layer repository-overview report for the ``/`` index page.

Honest-vacuous discipline: every aggregate section carries an explicit
:class:`OverviewState`. The inventory is driven by :data:`INVENTORY_REGISTRY`
(a tuple of :class:`KindContributor` over the store's :class:`WorldStoreStats`),
so the renderer iterates contributors and never enumerates kind names. Sections
the system cannot yet answer report ``state=NOT_IMPLEMENTED`` with an explanatory
sentence rather than fabricating data or silently omitting the row.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from propstore.app.rendering import RenderPolicySummary, summarize_render_policy
from propstore.core.store_results import WorldStoreStats
from propstore.reporting import JsonReportMixin
from propstore.world import RenderPolicy, WorldQuery


class OverviewState(StrEnum):
    KNOWN = "known"
    VACUOUS = "vacuous"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass(frozen=True)
class InventoryRow:
    kind: str
    count: int
    state: OverviewState
    sentence: str
    href: str | None


@dataclass(frozen=True)
class OverviewSection:
    state: OverviewState
    sentence: str


@dataclass(frozen=True)
class RepositoryOverviewReport(JsonReportMixin):
    render_policy: RenderPolicySummary
    inventory_rows: tuple[InventoryRow, ...]
    provenance_summary: OverviewSection
    recent_activity: OverviewSection
    notable_conflicts: OverviewSection
    prose_summary: str


@dataclass(frozen=True)
class KindContributor:
    kind: str
    href: str | None
    count: Callable[[WorldStoreStats], int]


INVENTORY_REGISTRY: tuple[KindContributor, ...] = (
    KindContributor(
        kind="concepts", href="/concepts", count=lambda stats: stats.concepts
    ),
    KindContributor(kind="claims", href="/claims", count=lambda stats: stats.claims),
    KindContributor(kind="conflicts", href=None, count=lambda stats: stats.conflicts),
)


def build_repository_overview(
    world: WorldQuery, *, policy: RenderPolicy
) -> RepositoryOverviewReport:
    """Render the KB-stats / reasoning-inventory overview over the store stats."""

    stats = world.stats()
    summary = summarize_render_policy(policy)
    inventory_rows = tuple(
        _inventory_row(contributor, stats) for contributor in INVENTORY_REGISTRY
    )
    return RepositoryOverviewReport(
        render_policy=summary,
        inventory_rows=inventory_rows,
        provenance_summary=OverviewSection(
            state=OverviewState.NOT_IMPLEMENTED,
            sentence="Provenance aggregation is not yet computed.",
        ),
        recent_activity=OverviewSection(
            state=OverviewState.NOT_IMPLEMENTED,
            sentence="Recent activity aggregation is not yet computed.",
        ),
        notable_conflicts=OverviewSection(
            state=OverviewState.NOT_IMPLEMENTED,
            sentence="Notable conflicts are not yet computed.",
        ),
        prose_summary=_compose_prose(inventory_rows, summary),
    )


def _inventory_row(
    contributor: KindContributor, stats: WorldStoreStats
) -> InventoryRow:
    count = contributor.count(stats)
    return InventoryRow(
        kind=contributor.kind,
        count=count,
        state=OverviewState.KNOWN,
        sentence=f"{count} {contributor.kind} present.",
        href=contributor.href,
    )


def _compose_prose(
    inventory_rows: tuple[InventoryRow, ...], policy: RenderPolicySummary
) -> str:
    total = sum(row.count for row in inventory_rows)
    return (
        f"Repository holds {total} indexed entries across {len(inventory_rows)} "
        f"inventory kinds under {policy.semantics} semantics."
    )

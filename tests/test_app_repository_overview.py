"""Construction tests for the repository-overview app-layer report shapes.

These tests pin the dataclass surface for the `/`-index page report. Per
plan, only the dataclasses live here at this step — `build_repository_overview`
is added in a later step.
"""

from __future__ import annotations

import dataclasses
from typing import get_args

import pytest

from propstore.app.rendering import RenderPolicySummary
from propstore.app.repository_overview import (
    InventoryRow,
    NotableConflictPointer,
    NotableConflicts,
    OverviewState,
    ProvenanceStateCount,
    ProvenanceSummary,
    RecentActivity,
    RecentActivityEntry,
    RepositoryOverviewReport,
    RepositoryOverviewRequest,
    SourcePointer,
)
from propstore.app.rendering import AppRenderPolicyRequest
from propstore.app.repository_views import AppRepositoryViewRequest


def _render_policy_summary() -> RenderPolicySummary:
    return RenderPolicySummary(
        reasoning_backend="claim_graph",
        strategy="default",
        semantics="grounded",
        set_comparison="elitist",
        decision_criterion="pignistic",
        pessimism_index=0.5,
        praf_strategy="auto",
        praf_epsilon=0.01,
        praf_confidence=0.95,
        praf_seed=None,
        include_drafts=False,
        include_blocked=False,
        show_quarantined=False,
    )


def test_overview_state_alias_admits_only_documented_values() -> None:
    assert set(get_args(OverviewState)) == {"known", "vacuous", "not_implemented"}


def test_repository_overview_request_is_frozen_with_default_subrequests() -> None:
    request = RepositoryOverviewRequest()

    assert dataclasses.is_dataclass(request)
    assert isinstance(request.render_policy, AppRenderPolicyRequest)
    assert isinstance(request.repository_view, AppRepositoryViewRequest)

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.render_policy = AppRenderPolicyRequest()  # type: ignore[misc]


def test_inventory_row_carries_kind_count_state_sentence_href() -> None:
    row = InventoryRow(
        kind="claims",
        count=42,
        state="known",
        sentence="42 claims are present in the sidecar.",
        href="/claims",
    )

    assert row.kind == "claims"
    assert row.count == 42
    assert row.state == "known"
    assert row.sentence == "42 claims are present in the sidecar."
    assert row.href == "/claims"

    with pytest.raises(dataclasses.FrozenInstanceError):
        row.count = 43  # type: ignore[misc]


def test_inventory_row_admits_none_href_for_kinds_without_route() -> None:
    row = InventoryRow(
        kind="unrouted",
        count=0,
        state="vacuous",
        sentence="No canonical web page for this kind yet.",
        href=None,
    )

    assert row.href is None


def test_source_pointer_construction_and_state() -> None:
    pointer = SourcePointer(
        state="known",
        source_id="src-1",
        slug="paper-foo",
        kind="paper",
        sentence="Paper foo, 3 claims.",
        href="/source/src-1",
    )

    assert pointer.state == "known"
    assert pointer.source_id == "src-1"
    assert pointer.slug == "paper-foo"
    assert pointer.kind == "paper"
    assert pointer.href == "/source/src-1"


def test_provenance_summary_with_state_counts() -> None:
    counts = (
        ProvenanceStateCount(state="measured", count=10),
        ProvenanceStateCount(state="calibrated", count=3),
        ProvenanceStateCount(state="vacuous", count=8),
    )
    summary = ProvenanceSummary(
        state="known",
        counts=counts,
        sentence="21 claims across 3 provenance states.",
    )

    assert summary.state == "known"
    assert summary.counts == counts
    assert isinstance(summary.counts, tuple)


def test_provenance_summary_can_be_not_implemented() -> None:
    summary = ProvenanceSummary(
        state="not_implemented",
        counts=(),
        sentence="Provenance aggregation is not yet computed.",
    )

    assert summary.state == "not_implemented"
    assert summary.counts == ()


def test_recent_activity_entry_construction() -> None:
    entry = RecentActivityEntry(
        when="2026-05-02T19:40:32",
        what="Added claim X",
        href="/claim/x",
    )

    assert entry.when == "2026-05-02T19:40:32"
    assert entry.what == "Added claim X"
    assert entry.href == "/claim/x"


def test_recent_activity_with_entries() -> None:
    activity = RecentActivity(
        state="known",
        entries=(
            RecentActivityEntry(when="2026-05-02", what="x", href=None),
        ),
        sentence="1 recent change.",
    )

    assert activity.state == "known"
    assert isinstance(activity.entries, tuple)
    assert len(activity.entries) == 1


def test_notable_conflict_pointer_construction() -> None:
    pointer = NotableConflictPointer(
        claim_id="c1",
        sentence="claim c1 is attacked by 2 claims.",
        href="/claim/c1",
    )

    assert pointer.claim_id == "c1"
    assert pointer.href == "/claim/c1"


def test_notable_conflicts_with_pointers() -> None:
    conflicts = NotableConflicts(
        state="known",
        entries=(
            NotableConflictPointer(claim_id="c1", sentence="x", href=None),
        ),
        sentence="1 contested claim.",
    )

    assert conflicts.state == "known"
    assert len(conflicts.entries) == 1


def test_repository_overview_report_carries_all_typed_sections() -> None:
    policy = _render_policy_summary()
    report = RepositoryOverviewReport(
        repository_state="current worktree",
        render_policy=policy,
        inventory_rows=(
            InventoryRow(
                kind="claims",
                count=42,
                state="known",
                sentence="42 claims.",
                href="/claims",
            ),
        ),
        source_pointers=(),
        provenance_summary=ProvenanceSummary(
            state="not_implemented",
            counts=(),
            sentence="not yet computed",
        ),
        recent_activity=RecentActivity(
            state="not_implemented",
            entries=(),
            sentence="not yet computed",
        ),
        notable_conflicts=NotableConflicts(
            state="not_implemented",
            entries=(),
            sentence="not yet computed",
        ),
        prose_summary="The repository holds 42 claims under grounded semantics.",
    )

    assert dataclasses.is_dataclass(report)
    assert report.repository_state == "current worktree"
    assert report.render_policy is policy
    assert isinstance(report.inventory_rows, tuple)
    assert report.inventory_rows[0].kind == "claims"
    assert isinstance(report.source_pointers, tuple)
    assert report.provenance_summary.state == "not_implemented"
    assert report.recent_activity.state == "not_implemented"
    assert report.notable_conflicts.state == "not_implemented"
    assert "42 claims" in report.prose_summary

    with pytest.raises(dataclasses.FrozenInstanceError):
        report.repository_state = "other"  # type: ignore[misc]

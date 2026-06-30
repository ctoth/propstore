"""Repository-overview report over the store stats (Phase 10-0)."""

from __future__ import annotations

from pathlib import Path

from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.app.repository_overview import (
    OverviewState,
    build_repository_overview,
)
from propstore.world import WorldQuery
from tests.app_render_helpers import build_demo_repo


def test_inventory_rows_count_concepts_and_claims(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_repository_overview(
            world, policy=build_render_policy(AppRenderPolicyRequest())
        )
    counts = {row.kind: row.count for row in report.inventory_rows}
    assert counts["concepts"] == 3
    assert counts["claims"] == 7
    assert "conflicts" in counts
    assert all(row.state is OverviewState.KNOWN for row in report.inventory_rows)


def test_unimplemented_sections_are_honest(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_repository_overview(
            world, policy=build_render_policy(AppRenderPolicyRequest())
        )
    assert report.provenance_summary.state is OverviewState.NOT_IMPLEMENTED
    assert report.recent_activity.state is OverviewState.NOT_IMPLEMENTED
    assert report.notable_conflicts.state is OverviewState.NOT_IMPLEMENTED


def test_prose_summary_mentions_totals(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_repository_overview(
            world, policy=build_render_policy(AppRenderPolicyRequest())
        )
    assert "indexed entries" in report.prose_summary
    assert "grounded" in report.prose_summary


def test_report_is_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_repository_overview(
            world, policy=build_render_policy(AppRenderPolicyRequest())
        )
    payload = report.to_json()
    assert isinstance(payload["inventory_rows"], list)
    assert payload["provenance_summary"]["state"] == "not_implemented"

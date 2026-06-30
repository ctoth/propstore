"""Single-claim view + claim list/search summary (Phase 10-0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.claim_views import (
    ClaimViewBlockedError,
    ClaimViewUnknownClaimError,
    build_claim_view,
)
from propstore.app.claims import list_claim_views, search_claim_views
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.app.view_state import ViewState
from propstore.world import RenderPolicy, WorldQuery
from tests.app_render_helpers import build_demo_repo


def _default_policy() -> RenderPolicy:
    return build_render_policy(AppRenderPolicyRequest())


def _include_all_policy() -> RenderPolicy:
    return build_render_policy(
        AppRenderPolicyRequest(include_drafts=True, include_blocked=True)
    )


def test_known_value_concept_and_condition(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_claim_view(world, "p_speed", policy=_default_policy())
    assert report.concept.state is ViewState.KNOWN
    assert report.concept.canonical_name == "Speed"
    assert report.concept.form == "velocity"
    assert report.value.state is ViewState.KNOWN
    assert report.value.value == 3.0
    assert report.value.sentence == "Value is 3.0 m/s."
    assert report.condition.state is ViewState.KNOWN
    assert report.condition.expression == "speed > 0"
    assert report.uncertainty.state is ViewState.KNOWN
    assert report.status.state is ViewState.KNOWN
    assert report.provenance.state is ViewState.MISSING


def test_missing_value_on_scalar_claim(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_claim_view(world, "p_missingval", policy=_default_policy())
    assert report.value.state is ViewState.MISSING
    assert report.value.sentence == "Value is missing."


def test_value_not_applicable_for_equation(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_claim_view(world, "eq1", policy=_default_policy())
    assert report.value.state is ViewState.NOT_APPLICABLE
    assert report.concept.state is ViewState.NOT_APPLICABLE
    assert report.condition.state is ViewState.VACUOUS


def test_unknown_claim_raises(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(ClaimViewUnknownClaimError):
            build_claim_view(world, "does-not-exist", policy=_default_policy())


def test_blocked_claim_raises_under_default_policy(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(ClaimViewBlockedError):
            build_claim_view(world, "p_blocked", policy=_default_policy())


def test_blocked_claim_visible_when_included(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_claim_view(world, "p_blocked", policy=_include_all_policy())
    assert report.status.visible_under_policy is True
    assert report.status.claim_status == "blocked"


def test_list_hides_draft_and_blocked_by_default(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_claim_views(world, policy=_default_policy())
    ids = {entry.claim_id for entry in report.entries}
    assert "p_blocked" not in ids
    assert "p_draft" not in ids
    assert "p_speed" in ids


def test_list_includes_hidden_when_opted_in(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_claim_views(world, policy=_include_all_policy())
    ids = {entry.claim_id for entry in report.entries}
    assert {"p_blocked", "p_draft"} <= ids


def test_list_scoped_to_concept(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_claim_views(world, policy=_default_policy(), concept="speed")
    ids = {entry.claim_id for entry in report.entries}
    assert "p_speed" in ids
    assert "p_missingval" not in ids  # that one is about distance


def test_summary_value_displays(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = list_claim_views(world, policy=_default_policy())
    by_id = {entry.claim_id: entry for entry in report.entries}
    assert by_id["p_speed"].value_display == "3.0 m/s"
    assert by_id["eq1"].value_display == "v = d / t"
    assert by_id["p_missingval"].value_display == "(missing)"
    # eq1 lists its variable concepts, so the display names them.
    assert by_id["eq1"].concept_display == "Speed, Distance"


def test_search_matches_statement(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = search_claim_views(world, "friction", policy=_default_policy())
    ids = {entry.claim_id for entry in report.entries}
    assert ids == {"mech1"}


def test_search_respects_limit(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = search_claim_views(world, "", policy=_default_policy(), limit=2)
    assert len(report.entries) == 2

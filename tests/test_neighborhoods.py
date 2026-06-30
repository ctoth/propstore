"""Semantic neighborhood report — claim focus only (Phase 10-0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.app.claim_views import ClaimViewBlockedError, ClaimViewUnknownClaimError
from propstore.app.neighborhoods import (
    SemanticNeighborhoodUnsupportedFocusError,
    build_semantic_neighborhood,
)
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
from propstore.app.view_state import ViewState
from propstore.world import RenderPolicy, WorldQuery
from tests.app_render_helpers import build_demo_repo


def _default_policy() -> RenderPolicy:
    return build_render_policy(AppRenderPolicyRequest())


def _move(report, kind: str):
    return next(move for move in report.moves if move.kind == kind)


def test_supporters_and_attackers(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_semantic_neighborhood(
            world, "claim", "p_speed", policy=_default_policy()
        )
    assert report.focus.focus_id == "p_speed"
    assert report.status.state is ViewState.KNOWN
    assert _move(report, "supporters").target_ids == ("o_speed",)
    assert _move(report, "attackers").target_ids == ("eq1",)


def test_shared_concept_excludes_self_and_hidden(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_semantic_neighborhood(
            world, "claim", "p_speed", policy=_default_policy()
        )
    shared = set(_move(report, "shared_concept").target_ids)
    assert "p_speed" not in shared
    assert "p_draft" not in shared  # draft hidden under default policy
    assert {"o_speed", "mech1"} <= shared


def test_edges_carry_stance_kind_and_sentence(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_semantic_neighborhood(
            world, "claim", "p_speed", policy=_default_policy()
        )
    kinds = {edge.edge_kind for edge in report.edges}
    assert {"supports", "rebuts"} <= kinds
    assert all(edge.sentence for edge in report.edges)


def test_unsupported_focus_kind_raises(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(SemanticNeighborhoodUnsupportedFocusError):
            build_semantic_neighborhood(
                world, "concept", "speed", policy=_default_policy()
            )


def test_unknown_focus_claim_raises(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(ClaimViewUnknownClaimError):
            build_semantic_neighborhood(
                world, "claim", "nope", policy=_default_policy()
            )


def test_blocked_focus_claim_raises(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        with pytest.raises(ClaimViewBlockedError):
            build_semantic_neighborhood(
                world, "claim", "p_blocked", policy=_default_policy()
            )


def test_report_is_json_ready(tmp_path: Path) -> None:
    repo = build_demo_repo(tmp_path)
    with WorldQuery(repo) as world:
        report = build_semantic_neighborhood(
            world, "claim", "p_speed", policy=_default_policy()
        )
    payload = report.to_json()
    assert payload["focus"]["focus_id"] == "p_speed"
    assert isinstance(payload["table_rows"], list)

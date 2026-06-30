"""The single flag->policy construction path (Phase 10-0)."""

from __future__ import annotations

import pytest

from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicyValidationError,
    build_render_policy,
    summarize_render_policy,
)
from propstore.world import ResolutionStrategy
from propstore.world.types import ArgumentationSemantics


def test_default_request_builds_default_policy() -> None:
    policy = build_render_policy(AppRenderPolicyRequest())
    assert policy.include_drafts is False
    assert policy.include_blocked is False
    assert policy.show_quarantined is False
    assert policy.strategy is None
    assert policy.semantics is ArgumentationSemantics.GROUNDED


def test_lifecycle_flags_flow_through() -> None:
    policy = build_render_policy(
        AppRenderPolicyRequest(
            include_drafts=True, include_blocked=True, show_quarantined=True
        )
    )
    assert policy.include_drafts is True
    assert policy.include_blocked is True
    assert policy.show_quarantined is True


def test_strategy_string_normalizes_to_enum() -> None:
    policy = build_render_policy(AppRenderPolicyRequest(strategy="recency"))
    assert policy.strategy is ResolutionStrategy.RECENCY


def test_invalid_strategy_raises_validation_error() -> None:
    with pytest.raises(RenderPolicyValidationError):
        build_render_policy(AppRenderPolicyRequest(strategy="not-a-strategy"))


def test_invalid_semantics_raises_validation_error() -> None:
    with pytest.raises(RenderPolicyValidationError):
        build_render_policy(AppRenderPolicyRequest(semantics="not-a-semantics"))


def test_summary_reports_default_strategy_label() -> None:
    summary = summarize_render_policy(build_render_policy(AppRenderPolicyRequest()))
    assert summary.strategy == "default"
    assert summary.semantics == "grounded"


def test_summary_is_json_ready() -> None:
    summary = summarize_render_policy(
        build_render_policy(AppRenderPolicyRequest(include_drafts=True))
    )
    payload = summary.to_json()
    assert payload["include_drafts"] is True
    assert payload["strategy"] == "default"

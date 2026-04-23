from __future__ import annotations

import pytest

from propstore.app.rendering import (
    AppRenderPolicyRequest,
    RenderPolicyValidationError,
    build_render_policy,
    summarize_render_policy,
)
from propstore.world import ReasoningBackend, ResolutionStrategy
from propstore.world.types import ArgumentationSemantics


def test_build_render_policy_normalizes_request_values() -> None:
    policy = build_render_policy(
        AppRenderPolicyRequest(
            reasoning_backend="praf",
            strategy="argumentation",
            semantics="complete",
            set_comparison="democratic",
            decision_criterion="hurwicz",
            pessimism_index=0.7,
            praf_strategy="mc",
            praf_epsilon=0.02,
            praf_confidence=0.9,
            praf_seed=42,
            include_drafts=True,
            include_blocked=True,
            show_quarantined=True,
        )
    )

    assert policy.reasoning_backend is ReasoningBackend.PRAF
    assert policy.strategy is ResolutionStrategy.ARGUMENTATION
    assert policy.semantics is ArgumentationSemantics.COMPLETE
    assert policy.comparison == "democratic"
    assert policy.decision_criterion == "hurwicz"
    assert policy.pessimism_index == pytest.approx(0.7)
    assert policy.praf_strategy == "mc"
    assert policy.praf_mc_epsilon == pytest.approx(0.02)
    assert policy.praf_mc_confidence == pytest.approx(0.9)
    assert policy.praf_mc_seed == 42
    assert policy.include_drafts is True
    assert policy.include_blocked is True
    assert policy.show_quarantined is True


def test_summarize_render_policy_preserves_serializable_policy_state() -> None:
    policy = build_render_policy(
        AppRenderPolicyRequest(
            strategy="sample_size",
            include_blocked=True,
        )
    )

    summary = summarize_render_policy(policy)

    assert summary.strategy == "sample_size"
    assert summary.reasoning_backend == "claim_graph"
    assert summary.semantics == "grounded"
    assert summary.include_drafts is False
    assert summary.include_blocked is True
    assert summary.show_quarantined is False


def test_build_render_policy_reports_invalid_values_as_app_errors() -> None:
    with pytest.raises(RenderPolicyValidationError, match="Unknown reasoning_backend"):
        build_render_policy(AppRenderPolicyRequest(reasoning_backend="missing"))

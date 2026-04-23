"""Application-layer render policy construction."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.world import RenderPolicy, ResolutionStrategy
from propstore.world.types import (
    normalize_argumentation_semantics,
    normalize_reasoning_backend,
)


class RenderPolicyAppError(Exception):
    """Base class for expected render-policy app failures."""


class RenderPolicyValidationError(RenderPolicyAppError):
    """Raised when a render-policy request cannot be normalized."""


@dataclass(frozen=True)
class AppRenderPolicyRequest:
    reasoning_backend: str = "claim_graph"
    strategy: str | None = None
    semantics: str = "grounded"
    set_comparison: str = "elitist"
    decision_criterion: str = "pignistic"
    pessimism_index: float = 0.5
    praf_strategy: str = "auto"
    praf_epsilon: float = 0.01
    praf_confidence: float = 0.95
    praf_seed: int | None = None
    include_drafts: bool = False
    include_blocked: bool = False
    show_quarantined: bool = False


@dataclass(frozen=True)
class RenderPolicySummary:
    reasoning_backend: str
    strategy: str
    semantics: str
    set_comparison: str
    decision_criterion: str
    pessimism_index: float
    praf_strategy: str
    praf_epsilon: float
    praf_confidence: float
    praf_seed: int | None
    include_drafts: bool
    include_blocked: bool
    show_quarantined: bool


def build_render_policy(request: AppRenderPolicyRequest) -> RenderPolicy:
    """Normalize an app render-policy request into the domain policy object."""

    try:
        reasoning_backend = normalize_reasoning_backend(request.reasoning_backend)
        semantics = normalize_argumentation_semantics(request.semantics)
        strategy = (
            None
            if request.strategy is None
            else ResolutionStrategy(request.strategy)
        )
        return RenderPolicy(
            reasoning_backend=reasoning_backend,
            strategy=strategy,
            semantics=semantics,
            comparison=request.set_comparison,
            decision_criterion=request.decision_criterion,
            pessimism_index=request.pessimism_index,
            praf_strategy=request.praf_strategy,
            praf_mc_epsilon=request.praf_epsilon,
            praf_mc_confidence=request.praf_confidence,
            praf_mc_seed=request.praf_seed,
            include_drafts=request.include_drafts,
            include_blocked=request.include_blocked,
            show_quarantined=request.show_quarantined,
        )
    except (TypeError, ValueError) as exc:
        raise RenderPolicyValidationError(str(exc)) from exc


def summarize_render_policy(policy: RenderPolicy) -> RenderPolicySummary:
    """Return a web/API-safe summary of a normalized render policy."""

    return RenderPolicySummary(
        reasoning_backend=policy.reasoning_backend.value,
        strategy="default" if policy.strategy is None else policy.strategy.value,
        semantics=policy.semantics.value,
        set_comparison=policy.comparison,
        decision_criterion=policy.decision_criterion,
        pessimism_index=policy.pessimism_index,
        praf_strategy=policy.praf_strategy,
        praf_epsilon=policy.praf_mc_epsilon,
        praf_confidence=policy.praf_mc_confidence,
        praf_seed=policy.praf_mc_seed,
        include_drafts=policy.include_drafts,
        include_blocked=policy.include_blocked,
        show_quarantined=policy.show_quarantined,
    )

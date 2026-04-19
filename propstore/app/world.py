"""Application-layer world workflows.

This module owns repository-bound world use cases.  Lower-level
``propstore.world`` modules still own the model algorithms and report
shapes; the app layer opens the model, constructs policies, and exposes
entry points usable by CLI, web, or other presentation adapters.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from propstore.core.id_types import to_context_id
from propstore.repository import Repository
from propstore.world import Environment, RenderPolicy
from propstore.world.queries import (
    WorldAlgorithmsReport,
    WorldAlgorithmsRequest,
    WorldBindReport,
    WorldBindRequest,
    WorldConceptQueryReport,
    WorldConceptQueryRequest,
    WorldDeriveReport,
    WorldDeriveRequest,
    WorldExplainReport,
    WorldExplainRequest,
    WorldResolveReport,
    WorldResolveRequest,
    WorldStatusReport,
    WorldStatusRequest,
    derive_world_value,
    explain_world_claim,
    get_world_status,
    list_world_algorithms,
    query_bound_world,
    query_world_concept,
    resolve_world_value,
)

if TYPE_CHECKING:
    from propstore.world import BoundWorld, WorldModel


class WorldAppError(Exception):
    """Base class for expected app-layer world failures."""


class WorldSidecarMissingError(WorldAppError):
    def __init__(self) -> None:
        super().__init__("Sidecar not found. Run 'pks build' first.")


class WorldBindingParseError(WorldAppError):
    pass


@dataclass(frozen=True)
class WorldLifecycleOptions:
    include_drafts: bool = False
    include_blocked: bool = False
    show_quarantined: bool = False


@dataclass(frozen=True)
class AppWorldStatusRequest:
    lifecycle: WorldLifecycleOptions = field(default_factory=WorldLifecycleOptions)


@dataclass(frozen=True)
class AppWorldConceptQueryRequest:
    target: str
    lifecycle: WorldLifecycleOptions = field(default_factory=WorldLifecycleOptions)


@dataclass(frozen=True)
class AppWorldBindRequest:
    bindings: Mapping[str, str]
    target: str | None = None


@dataclass(frozen=True)
class AppWorldExplainRequest:
    claim_id: str


@dataclass(frozen=True)
class AppWorldAlgorithmsRequest:
    stage: str | None = None
    concept: str | None = None


@dataclass(frozen=True)
class AppWorldDeriveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    lifecycle: WorldLifecycleOptions = field(default_factory=WorldLifecycleOptions)


@dataclass(frozen=True)
class AppWorldResolveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    strategy: str
    override_id: str | None = None
    semantics: str = "grounded"
    set_comparison: str = "elitist"
    decision_criterion: str = "pignistic"
    pessimism_index: float = 0.5
    reasoning_backend: str = "claim_graph"
    praf_strategy: str = "auto"
    praf_epsilon: float = 0.01
    praf_confidence: float = 0.95
    praf_seed: int | None = None
    lifecycle: WorldLifecycleOptions = field(default_factory=WorldLifecycleOptions)


def lifecycle_policy(
    options: WorldLifecycleOptions,
    *,
    base: RenderPolicy | None = None,
) -> RenderPolicy:
    """Construct or clone a render policy with lifecycle visibility set."""

    if base is None:
        return RenderPolicy(
            include_drafts=options.include_drafts,
            include_blocked=options.include_blocked,
            show_quarantined=options.show_quarantined,
        )
    return replace(
        base,
        include_drafts=options.include_drafts,
        include_blocked=options.include_blocked,
        show_quarantined=options.show_quarantined,
    )


@contextmanager
def open_app_world_model(repo: Repository) -> Iterator[WorldModel]:
    from propstore.world import WorldModel

    try:
        world = WorldModel(repo)
    except FileNotFoundError as exc:
        raise WorldSidecarMissingError() from exc
    try:
        yield world
    finally:
        world.close()


def bind_world(
    world: WorldModel,
    bindings: Mapping[str, str],
    *,
    context_id: str | None = None,
    policy: RenderPolicy | None = None,
) -> "BoundWorld":
    environment = Environment(
        bindings=dict(bindings),
        context_id=(None if context_id is None else to_context_id(context_id)),
    )
    return world.bind(environment=environment, policy=policy)


def resolve_world_target(world: WorldModel, target: str) -> str:
    return world.resolve_concept(target) or target


def parse_world_binding_args(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse raw command-style binding tokens into bindings and target.

    Tokens containing ``=`` become string key/value bindings.  The last
    token without ``=`` is treated as the optional world target.
    """

    parsed: dict[str, str] = {}
    remaining: list[str] = []
    for arg in args:
        if "=" not in arg:
            remaining.append(arg)
            continue
        key, _, value = arg.partition("=")
        if not key:
            raise WorldBindingParseError("world bindings require a non-empty key")
        parsed[key] = value
    return parsed, remaining[-1] if remaining else None


def world_status(
    repo: Repository,
    request: AppWorldStatusRequest,
) -> WorldStatusReport:
    with open_app_world_model(repo) as world:
        return get_world_status(
            world,
            WorldStatusRequest(policy=lifecycle_policy(request.lifecycle)),
        )


def world_concept_query(
    repo: Repository,
    request: AppWorldConceptQueryRequest,
) -> WorldConceptQueryReport:
    with open_app_world_model(repo) as world:
        return query_world_concept(
            world,
            WorldConceptQueryRequest(
                target=request.target,
                policy=lifecycle_policy(request.lifecycle),
            ),
        )


def world_bind(
    repo: Repository,
    request: AppWorldBindRequest,
) -> WorldBindReport:
    with open_app_world_model(repo) as world:
        return query_bound_world(
            world,
            WorldBindRequest(bindings=request.bindings, target=request.target),
        )


def world_explain(
    repo: Repository,
    request: AppWorldExplainRequest,
) -> WorldExplainReport:
    with open_app_world_model(repo) as world:
        return explain_world_claim(
            world,
            WorldExplainRequest(claim_id=request.claim_id),
        )


def world_algorithms(
    repo: Repository,
    request: AppWorldAlgorithmsRequest,
) -> WorldAlgorithmsReport:
    with open_app_world_model(repo) as world:
        return list_world_algorithms(
            world,
            WorldAlgorithmsRequest(stage=request.stage, concept=request.concept),
        )


def world_derive(
    repo: Repository,
    request: AppWorldDeriveRequest,
) -> WorldDeriveReport:
    with open_app_world_model(repo) as world:
        return derive_world_value(
            world,
            WorldDeriveRequest(
                concept_id=request.concept_id,
                bindings=request.bindings,
                policy=lifecycle_policy(request.lifecycle),
            ),
        )


def world_resolve(
    repo: Repository,
    request: AppWorldResolveRequest,
) -> WorldResolveReport:
    from propstore.world import ResolutionStrategy
    from propstore.world.types import (
        normalize_argumentation_semantics,
        normalize_reasoning_backend,
    )

    with open_app_world_model(repo) as world:
        resolved = resolve_world_target(world, request.concept_id)
        policy = RenderPolicy(
            reasoning_backend=normalize_reasoning_backend(request.reasoning_backend),
            strategy=ResolutionStrategy(request.strategy),
            semantics=normalize_argumentation_semantics(request.semantics),
            comparison=request.set_comparison,
            decision_criterion=request.decision_criterion,
            pessimism_index=request.pessimism_index,
            praf_strategy=request.praf_strategy,
            praf_mc_epsilon=request.praf_epsilon,
            praf_mc_confidence=request.praf_confidence,
            praf_mc_seed=request.praf_seed,
            overrides={} if request.override_id is None else {resolved: request.override_id},
            include_drafts=request.lifecycle.include_drafts,
            include_blocked=request.lifecycle.include_blocked,
            show_quarantined=request.lifecycle.show_quarantined,
        )
        return resolve_world_value(
            world,
            WorldResolveRequest(
                concept_id=request.concept_id,
                bindings=request.bindings,
                policy=policy,
            ),
        )

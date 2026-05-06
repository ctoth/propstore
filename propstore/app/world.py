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
from propstore.app.rendering import AppRenderPolicyRequest, build_render_policy
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
    AmbiguousConceptError,
    WorldStatusReport,
    WorldStatusRequest,
    UnknownClaimError,
    UnknownConceptError,
    WorldBindActiveReport,
    WorldBindConceptReport,
    WorldResolveError,
    WorldHypotheticalReport,
    WorldHypotheticalRequest,
    WorldHypotheticalSyntheticClaimSpec,
    WorldChainReport,
    WorldChainRequest,
    derive_world_value,
    diff_hypothetical_world,
    explain_world_claim,
    get_world_status,
    list_world_algorithms,
    query_bound_world,
    query_world_chain,
    query_world_concept,
    resolve_world_value,
)

if TYPE_CHECKING:
    from propstore.world import BoundWorld, WorldQuery


class WorldAppError(Exception):
    """Base class for expected app-layer world failures."""


class WorldSidecarMissingError(WorldAppError):
    def __init__(self) -> None:
        super().__init__("Sidecar not found. Run 'pks build' first.")


@dataclass(frozen=True)
class AppWorldStatusRequest:
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


@dataclass(frozen=True)
class AppWorldConceptQueryRequest:
    target: str
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


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
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


@dataclass(frozen=True)
class AppWorldResolveRequest:
    concept_id: str
    bindings: Mapping[str, str]
    strategy: str
    override_id: str | None = None
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


@dataclass(frozen=True)
class AppWorldHypotheticalRequest:
    bindings: Mapping[str, str]
    remove_claim_ids: tuple[str, ...] = ()
    add_claims: tuple[WorldHypotheticalSyntheticClaimSpec, ...] = ()


@dataclass(frozen=True)
class AppWorldChainRequest:
    concept_id: str
    bindings: Mapping[str, str]
    strategy: str | None = None
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)


@dataclass(frozen=True)
class AppWorldExportGraphRequest:
    bindings: Mapping[str, str]
    group_id: int | None = None


@dataclass(frozen=True)
class AppWorldSensitivityRequest:
    concept_id: str
    bindings: Mapping[str, str]


@dataclass(frozen=True)
class AppWorldFragilityRequest:
    bindings: Mapping[str, str]
    context_id: str | None = None
    concept_id: str | None = None
    top_k: int = 20
    include_atms: bool = True
    include_discovery: bool = True
    include_conflict: bool = True
    include_grounding: bool = True
    include_bridge: bool = True
    ranking_policy: str = "heuristic_roi"


@dataclass(frozen=True)
class AppWorldConsistencyRequest:
    bindings: Mapping[str, str]
    transitive: bool = False


@contextmanager
def open_app_world_model(repo: Repository) -> Iterator[WorldQuery]:
    from propstore.world import WorldQuery

    try:
        world = WorldQuery(repo)
    except FileNotFoundError as exc:
        raise WorldSidecarMissingError() from exc
    try:
        yield world
    finally:
        world.close()


def bind_world(
    world: WorldQuery,
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


def resolve_world_target(world: WorldQuery, target: str) -> str:
    return world.resolve_concept(target) or target


def world_status(
    repo: Repository,
    request: AppWorldStatusRequest,
) -> WorldStatusReport:
    with open_app_world_model(repo) as world:
        report = get_world_status(
            world,
            WorldStatusRequest(policy=build_render_policy(request.render_policy)),
        )
    counts = _authored_world_counts(repo)
    return replace(
        report,
        source_count=counts["sources"],
        context_count=counts["contexts"],
        predicate_count=counts["predicates"],
        rule_count=counts["rules"],
        stance_count=counts["stances"],
    )


def _authored_world_counts(repo: Repository) -> dict[str, int]:
    return {
        "sources": sum(1 for _ in repo.families.sources.iter_handles()),
        "contexts": sum(1 for _ in repo.families.contexts.iter_handles()),
        "predicates": sum(
            len(handle.document.predicates)
            for handle in repo.families.predicates.iter_handles()
        ),
        "rules": sum(
            len(handle.document.rules)
            for handle in repo.families.rules.iter_handles()
        ),
        "stances": sum(
            len(handle.document.stances)
            for handle in repo.families.stances.iter_handles()
        ),
    }


def world_concept_query(
    repo: Repository,
    request: AppWorldConceptQueryRequest,
) -> WorldConceptQueryReport:
    with open_app_world_model(repo) as world:
        return query_world_concept(
            world,
            WorldConceptQueryRequest(
                target=request.target,
                policy=build_render_policy(request.render_policy),
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
                policy=build_render_policy(request.render_policy),
            ),
        )


def world_resolve(
    repo: Repository,
    request: AppWorldResolveRequest,
) -> WorldResolveReport:
    with open_app_world_model(repo) as world:
        resolved = resolve_world_target(world, request.concept_id)
        policy = replace(
            build_render_policy(
                replace(request.render_policy, strategy=request.strategy),
            ),
            overrides={} if request.override_id is None else {resolved: request.override_id},
        )
        return resolve_world_value(
            world,
            WorldResolveRequest(
                concept_id=request.concept_id,
                bindings=request.bindings,
                policy=policy,
            ),
        )


def world_hypothetical(
    repo: Repository,
    request: AppWorldHypotheticalRequest,
) -> WorldHypotheticalReport:
    with open_app_world_model(repo) as world:
        return diff_hypothetical_world(
            world,
            WorldHypotheticalRequest(
                bindings=request.bindings,
                remove_claim_ids=request.remove_claim_ids,
                add_claims=request.add_claims,
            ),
        )


def world_chain(
    repo: Repository,
    request: AppWorldChainRequest,
) -> WorldChainReport:
    # Chain currently does not consume RenderPolicy, but constructing the
    # policy here keeps lifecycle option validation in the app layer.
    _ = build_render_policy(request.render_policy)
    with open_app_world_model(repo) as world:
        return query_world_chain(
            world,
            WorldChainRequest(
                concept_id=request.concept_id,
                bindings=request.bindings,
                strategy=request.strategy,
            ),
        )


def world_export_graph(
    repo: Repository,
    request: AppWorldExportGraphRequest,
):
    from propstore.graph_export import GraphExportRequest, export_knowledge_graph

    with open_app_world_model(repo) as world:
        return export_knowledge_graph(
            world,
            GraphExportRequest(bindings=request.bindings, group_id=request.group_id),
        )


def world_sensitivity(
    repo: Repository,
    request: AppWorldSensitivityRequest,
):
    from propstore.sensitivity import SensitivityRequest, query_sensitivity

    with open_app_world_model(repo) as world:
        return query_sensitivity(
            world,
            SensitivityRequest(
                concept_id=request.concept_id,
                bindings=request.bindings,
            ),
        )


def world_fragility(
    repo: Repository,
    request: AppWorldFragilityRequest,
):
    from propstore.fragility import FragilityRequest, query_fragility

    with open_app_world_model(repo) as world:
        return query_fragility(
            world,
            FragilityRequest(
                bindings=request.bindings,
                context_id=request.context_id,
                concept_id=request.concept_id,
                top_k=request.top_k,
                include_atms=request.include_atms,
                include_discovery=request.include_discovery,
                include_conflict=request.include_conflict,
                include_grounding=request.include_grounding,
                include_bridge=request.include_bridge,
                ranking_policy=request.ranking_policy,
            ),
        )


def world_consistency(
    repo: Repository,
    request: AppWorldConsistencyRequest,
):
    from propstore.world.consistency import (
        WorldConsistencyRequest,
        check_world_consistency,
    )

    with open_app_world_model(repo) as world:
        return check_world_consistency(
            repo,
            world,
            WorldConsistencyRequest(
                bindings=request.bindings,
                transitive=request.transitive,
            ),
        )

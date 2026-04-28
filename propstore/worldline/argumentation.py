from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from propstore.canonical_json import canonical_dumps
from propstore.core.active_claims import ActiveClaim, coerce_active_claims
from propstore.core.id_types import ClaimId, to_claim_id
from propstore.core.labels import Label, SupportQuality
from propstore.core.row_types import StanceRow, coerce_stance_row
from propstore.core.environment import StanceStore
from propstore.world.types import (
    ClaimSupportView,
    HasATMSEngine,
    RenderPolicy,
    coerce_queryable_assumptions,
    validate_backend_semantics,
)
from propstore.worldline.definition import WorldlineDefinition
from propstore.worldline.interfaces import HasActiveGraph, WorldlineBoundView, WorldlineStore
from propstore.worldline.result_types import WorldlineArgumentationState


def capture_argumentation_state(
    bound: WorldlineBoundView,
    world: WorldlineStore,
    definition: WorldlineDefinition,
) -> tuple[WorldlineArgumentationState | None, list[str], set[ClaimId]]:
    from propstore.world.types import ReasoningBackend

    active = coerce_active_claims(bound.active_claims())
    active_ids = {claim.claim_id for claim in active}
    active_graph = bound._active_graph if isinstance(bound, HasActiveGraph) else None
    reasoning_backend = definition.policy.reasoning_backend
    _, normalized_semantics = validate_backend_semantics(
        reasoning_backend,
        definition.policy.semantics,
    )

    argumentation_state: WorldlineArgumentationState | None = None
    if (
        reasoning_backend == ReasoningBackend.CLAIM_GRAPH
        and world.has_table("relation_edge")
    ):
        argumentation_state = _capture_claim_graph(
            world,
            active_ids,
            active_graph,
            definition.policy,
            normalized_semantics,
        )
    elif (
        reasoning_backend == ReasoningBackend.ASPIC
        and world.has_table("relation_edge")
    ):
        argumentation_state = _capture_aspic(
            bound,
            world,
            active,
            active_ids,
            active_graph,
            definition.policy,
            normalized_semantics,
        )
    elif reasoning_backend == ReasoningBackend.ATMS:
        argumentation_state = _capture_atms(bound, definition.policy)
    elif (
        reasoning_backend == ReasoningBackend.PRAF
        and world.has_table("relation_edge")
    ):
        argumentation_state = _capture_praf(
            world,
            active_ids,
            active_graph,
            definition.policy,
            normalized_semantics,
        )

    stance_dependencies: list[str] = []
    if argumentation_state is not None and argumentation_state.backend != "atms":
        stance_dependencies = active_stance_dependencies(bound, world, active_ids)

    return argumentation_state, stance_dependencies, active_ids


def _capture_claim_graph(
    world: WorldlineStore,
    active_ids: set[ClaimId],
    active_graph: Any,
    policy: RenderPolicy,
    normalized_semantics: Any,
) -> WorldlineArgumentationState | None:
    justified_claims: frozenset[ClaimId] | None = None
    extension_claim_sets: tuple[frozenset[ClaimId], ...] = ()
    if active_graph is not None:
        from propstore.core.analyzers import (
            analyze_claim_graph,
            shared_analyzer_input_from_active_graph,
        )

        analyzer_result = analyze_claim_graph(
            shared_analyzer_input_from_active_graph(
                active_graph,
                comparison=policy.comparison,
            ),
            semantics=normalized_semantics,
        )
        extension_claim_sets = tuple(
            frozenset(
                to_claim_id(claim_id) for claim_id in extension.accepted_claim_ids
            )
            for extension in analyzer_result.extensions
        )
        if extension_claim_sets:
            justified_claims = _claims_for_inference_mode(
                extension_claim_sets,
                _worldline_inference_mode(normalized_semantics),
            )
    else:
        from propstore.claim_graph import compute_claim_graph_justified_claims

        current = compute_claim_graph_justified_claims(
            world,
            {str(claim_id) for claim_id in active_ids},
            semantics=normalized_semantics,
            comparison=policy.comparison,
        )
        if isinstance(current, frozenset):
            justified_claims = frozenset(
                to_claim_id(claim_id)
                for claim_id in current
            )
            extension_claim_sets = (justified_claims,)

    if justified_claims is None:
        return None
    defeated = active_ids - justified_claims
    return WorldlineArgumentationState(
        backend="claim_graph",
        justified=tuple(sorted(str(claim_id) for claim_id in justified_claims)),
        defeated=tuple(sorted(str(claim_id) for claim_id in defeated)),
        extensions=tuple(
            tuple(sorted(str(claim_id) for claim_id in extension))
            for extension in extension_claim_sets
        ),
        inference_mode=_worldline_inference_mode(normalized_semantics),
    )


def _worldline_inference_mode(normalized_semantics: Any) -> str:
    semantics_name = str(getattr(normalized_semantics, "value", normalized_semantics))
    return "grounded" if semantics_name == "grounded" else "credulous"


def _claims_for_inference_mode(
    extensions: tuple[frozenset[ClaimId], ...],
    inference_mode: str,
) -> frozenset[ClaimId]:
    if inference_mode == "grounded":
        return extensions[0]
    if inference_mode == "skeptical":
        return frozenset(set.intersection(*(set(extension) for extension in extensions)))
    return frozenset().union(*extensions)


def _capture_aspic(
    bound: WorldlineBoundView,
    world: WorldlineStore,
    active: list[ActiveClaim],
    active_ids: set[ClaimId],
    active_graph: Any,
    policy: RenderPolicy,
    normalized_semantics: Any,
) -> WorldlineArgumentationState | None:
    from propstore.world.types import ReasoningBackend
    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.structured_projection import (
        build_structured_projection,
        compute_structured_justified_arguments,
    )

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    if isinstance(bound, ClaimSupportView):
        for claim in active:
            support_metadata[str(claim.claim_id)] = bound.claim_support(claim)

    grounding_bundle = getattr(world, "grounding_bundle", None)
    if not callable(grounding_bundle):
        return None
    typed_grounding_bundle = cast(Callable[[], GroundedRulesBundle], grounding_bundle)

    projection = build_structured_projection(
        world,
        active,
        bundle=typed_grounding_bundle(),
        support_metadata=support_metadata,
        comparison=policy.comparison,
        link=policy.link,
        active_graph=active_graph,
    )
    justified_arguments = compute_structured_justified_arguments(
        projection,
        semantics=normalized_semantics,
        backend=ReasoningBackend.ASPIC,
    )
    if not isinstance(justified_arguments, frozenset):
        return None

    justified_claim_ids = {
        to_claim_id(claim_id)
        for arg_id in justified_arguments
        if (claim_id := projection.argument_to_claim_id.get(arg_id)) is not None
    }
    defeated = active_ids - justified_claim_ids
    return WorldlineArgumentationState(
        backend="aspic",
        justified=tuple(sorted(str(claim_id) for claim_id in justified_claim_ids)),
        defeated=tuple(sorted(str(claim_id) for claim_id in defeated)),
    )


def _capture_atms(
    bound: WorldlineBoundView,
    policy: RenderPolicy,
) -> WorldlineArgumentationState | None:
    if not isinstance(bound, HasATMSEngine):
        return None
    return WorldlineArgumentationState.from_mapping(
        bound.atms_engine().argumentation_state(
            queryables=coerce_queryable_assumptions(policy.future_queryables),
            future_limit=policy.future_limit or 8,
        )
    )


def _capture_praf(
    world: WorldlineStore,
    active_ids: set[ClaimId],
    active_graph: Any,
    policy: RenderPolicy,
    normalized_semantics: Any,
) -> WorldlineArgumentationState:
    praf_strategy = policy.praf_strategy or "auto"
    praf_mc_epsilon = policy.praf_mc_epsilon or 0.01
    praf_mc_confidence = policy.praf_mc_confidence or 0.95
    praf_treewidth_cutoff = policy.praf_treewidth_cutoff or 12
    praf_mc_seed = policy.praf_mc_seed

    if active_graph is not None:
        from propstore.core.analyzers import (
            analyze_praf,
            shared_analyzer_input_from_active_graph,
        )

        analyzer_result = analyze_praf(
            shared_analyzer_input_from_active_graph(
                active_graph,
                comparison=policy.comparison or "elitist",
            ),
            semantics=normalized_semantics,
            strategy=praf_strategy,
            query_kind="argument_acceptance",
            inference_mode="credulous",
            mc_epsilon=praf_mc_epsilon,
            mc_confidence=praf_mc_confidence,
            treewidth_cutoff=praf_treewidth_cutoff,
            rng_seed=praf_mc_seed,
        )
        metadata = dict(analyzer_result.metadata)
        acceptance_probs = dict(metadata["acceptance_probs"])
        strategy_used = metadata["strategy_used"]
        samples = metadata["samples"]
        confidence_interval_half = metadata["confidence_interval_half"]
    else:
        from argumentation.probabilistic import compute_probabilistic_acceptance
        from propstore.praf import build_praf

        praf = build_praf(
            world,
            {str(claim_id) for claim_id in active_ids},
            comparison=policy.comparison or "elitist",
        )
        result = compute_probabilistic_acceptance(
            praf.kernel,
            semantics=normalized_semantics,
            strategy=praf_strategy,
            query_kind="argument_acceptance",
            inference_mode="credulous",
            mc_epsilon=praf_mc_epsilon,
            mc_confidence=praf_mc_confidence,
            treewidth_cutoff=praf_treewidth_cutoff,
            rng_seed=praf_mc_seed,
        )
        acceptance_probs = (
            {}
            if result.acceptance_probs is None
            else dict(result.acceptance_probs)
        )
        strategy_used = result.strategy_used
        samples = result.samples
        confidence_interval_half = result.confidence_interval_half

    return WorldlineArgumentationState(
        backend="praf",
        acceptance_probs=acceptance_probs,
        strategy_used=strategy_used,
        samples=samples,
        confidence_interval_half=confidence_interval_half,
        semantics=normalized_semantics.value,
    )


def _stance_dependency_key(row: StanceRow) -> str:
    return canonical_dumps(row.to_dict())


def active_stance_dependencies(
    bound: WorldlineBoundView,
    world: WorldlineStore,
    active_ids: set[ClaimId],
) -> list[str]:
    active_graph = bound._active_graph if isinstance(bound, HasActiveGraph) else None
    graph_relation_types = {
        "rebuts",
        "undercuts",
        "undermines",
        "supersedes",
        "supports",
        "explains",
    }

    if active_graph is not None:
        stance_rows: list[StanceRow] = []
        for edge in active_graph.compiled.relations:
            if edge.relation_type not in graph_relation_types:
                continue
            if (
                to_claim_id(edge.source_id) not in active_ids
                or to_claim_id(edge.target_id) not in active_ids
            ):
                continue
            stance_rows.append(
                StanceRow.from_mapping(
                    {
                        "claim_id": edge.source_id,
                        "target_claim_id": edge.target_id,
                        "stance_type": edge.relation_type,
                        **dict(edge.attributes),
                    }
                )
            )
        return sorted(_stance_dependency_key(row) for row in stance_rows)

    if isinstance(world, StanceStore) and world.has_table("relation_edge"):
        return sorted(
            _stance_dependency_key(coerce_stance_row(row))
            for row in world.stances_between({str(claim_id) for claim_id in active_ids})
        )
    return []

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeGuard

import rfc8785
from propstore.core.active_claims import ActiveClaim, coerce_active_claims
from propstore.core.id_types import ClaimId, to_claim_id
from propstore.core.labels import Label, SupportQuality
from propstore.families.relations import Stance
from propstore.reporting import json_ready
from propstore.world.types import (
    ArgumentationSemantics,
    ClaimSupportView,
    GroundingBundleStore,
    HasActiveGraph,
    HasATMSEngine,
    RenderPolicy,
    coerce_queryable_assumptions,
    validate_backend_semantics,
)
from propstore.worldline.interfaces import WorldlineBoundView, WorldlineStore
from propstore.worldline.result_types import WorldlineArgumentationState


_STANCE_RELATION_TYPES = frozenset(
    {
        "rebuts",
        "undercuts",
        "undermines",
        "supersedes",
        "supports",
        "explains",
    }
)


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _semantics_value(normalized_semantics: Any) -> str:
    if isinstance(normalized_semantics, ArgumentationSemantics):
        return normalized_semantics.value
    return str(normalized_semantics)


def capture_argumentation_state(
    bound: WorldlineBoundView,
    world: WorldlineStore,
    policy: RenderPolicy,
) -> tuple[WorldlineArgumentationState | None, list[str], set[ClaimId]]:
    from propstore.world.types import ReasoningBackend

    active = coerce_active_claims(bound.active_claims())
    active_ids = {claim.claim_id for claim in active}
    active_graph = bound.active_world_graph() if isinstance(bound, HasActiveGraph) else None
    reasoning_backend = policy.reasoning_backend
    _, normalized_semantics = validate_backend_semantics(
        reasoning_backend,
        policy.semantics,
    )

    argumentation_state: WorldlineArgumentationState | None = None
    if reasoning_backend == ReasoningBackend.CLAIM_GRAPH:
        argumentation_state = _capture_claim_graph(
            world,
            {to_claim_id(claim_id) for claim_id in active_ids},
            active_graph,
            policy,
            normalized_semantics,
        )
    elif reasoning_backend == ReasoningBackend.ASPIC:
        argumentation_state = _capture_aspic(
            bound,
            world,
            list(active),
            {to_claim_id(claim_id) for claim_id in active_ids},
            active_graph,
            policy,
            normalized_semantics,
        )
    elif reasoning_backend == ReasoningBackend.ATMS:
        argumentation_state = _capture_atms(bound, policy)
    elif reasoning_backend == ReasoningBackend.PRAF:
        argumentation_state = _capture_praf(
            world,
            {to_claim_id(claim_id) for claim_id in active_ids},
            active_graph,
            policy,
            normalized_semantics,
        )

    stance_dependencies: list[str] = []
    if argumentation_state is not None and argumentation_state.backend != "atms":
        stance_dependencies = active_stance_dependencies(
            bound,
            world,
            {to_claim_id(claim_id) for claim_id in active_ids},
        )

    return argumentation_state, stance_dependencies, {to_claim_id(c) for c in active_ids}


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
            shared_analyzer_input_from_graph,
        )

        analyzer_result = analyze_claim_graph(
            shared_analyzer_input_from_graph(
                active_graph,
                comparison=policy.comparison,
            ),
            semantics=_semantics_value(normalized_semantics),
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
            semantics=_semantics_value(normalized_semantics),
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
        shared = set(extensions[0])
        for extension in extensions[1:]:
            shared &= set(extension)
        return frozenset(shared)
    return frozenset[ClaimId]().union(*extensions)


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
    from propstore.aspic_bridge import build_aspic_projection
    from propstore.structured_projection import compute_structured_justified_arguments

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    if isinstance(bound, ClaimSupportView):
        for claim in active:
            support_metadata[str(claim.claim_id)] = bound.claim_support(claim)

    if not isinstance(world, GroundingBundleStore):
        return None

    projection = build_aspic_projection(
        world,
        active,
        bundle=world.grounding_bundle(),
        support_metadata=support_metadata,
        comparison=policy.comparison,
        link=policy.link,
        active_graph=active_graph,
    )
    justified_arguments = compute_structured_justified_arguments(
        projection,
        semantics=_semantics_value(normalized_semantics),
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
    from propstore.core.analyzers import (
        analyze_praf,
        shared_analyzer_input_from_graph,
        shared_analyzer_input_from_store,
    )

    comparison = policy.comparison or "elitist"
    praf_strategy = policy.praf_strategy or "auto"
    praf_mc_epsilon = policy.praf_mc_epsilon or 0.01
    praf_mc_confidence = policy.praf_mc_confidence or 0.95
    praf_treewidth_cutoff = policy.praf_treewidth_cutoff or 12
    praf_mc_seed = policy.praf_mc_seed

    if active_graph is not None:
        shared = shared_analyzer_input_from_graph(
            active_graph,
            comparison=comparison,
        )
    else:
        shared = shared_analyzer_input_from_store(
            world,
            {str(claim_id) for claim_id in active_ids},
            comparison=comparison,
        )

    analyzer_result = analyze_praf(
        shared,
        semantics=_semantics_value(normalized_semantics),
        strategy=praf_strategy,
        query_kind="argument_acceptance",
        inference_mode="credulous",
        mc_epsilon=praf_mc_epsilon,
        mc_confidence=praf_mc_confidence,
        treewidth_cutoff=praf_treewidth_cutoff,
        rng_seed=praf_mc_seed,
    )
    metadata = dict(analyzer_result.metadata)
    raw_probs = metadata.get("acceptance_probs")
    acceptance_probs = (
        {str(key): float(value) for key, value in raw_probs.items()}
        if _is_mapping(raw_probs)
        else {}
    )
    strategy_used = metadata.get("strategy_used")
    samples = metadata.get("samples")
    confidence_interval_half = metadata.get("confidence_interval_half")

    return WorldlineArgumentationState(
        backend="praf",
        acceptance_probs=acceptance_probs,
        strategy_used=None if strategy_used is None else str(strategy_used),
        samples=None if samples is None else int(samples),
        confidence_interval_half=(
            None if confidence_interval_half is None else float(confidence_interval_half)
        ),
        semantics=_semantics_value(normalized_semantics),
    )


def _stance_dependency_key(payload: dict[str, Any]) -> str:
    return rfc8785.dumps(json_ready(payload)).decode("utf-8")


def _stance_key_from_charter(stance: Stance) -> dict[str, Any]:
    return {
        "source_claim_id": stance.source_claim_id,
        "target_claim_id": stance.target_claim_id,
        "stance_type": None if stance.stance_type is None else stance.stance_type.value,
        "resolution_model": stance.resolution_model,
        "confidence": stance.confidence,
        "opinion_belief": stance.opinion_belief,
        "opinion_disbelief": stance.opinion_disbelief,
        "opinion_uncertainty": stance.opinion_uncertainty,
        "opinion_base_rate": stance.opinion_base_rate,
    }


def active_stance_dependencies(
    bound: WorldlineBoundView,
    world: WorldlineStore,
    active_ids: set[ClaimId],
) -> list[str]:
    active_graph = bound.active_world_graph() if isinstance(bound, HasActiveGraph) else None

    if active_graph is not None:
        payloads: list[dict[str, Any]] = []
        for stance in active_graph.compiled.stances:
            if stance.source_claim_id is None or stance.target_claim_id is None:
                continue
            if stance.stance_type is None:
                continue
            if stance.stance_type.value not in _STANCE_RELATION_TYPES:
                continue
            if (
                to_claim_id(stance.source_claim_id) not in active_ids
                or to_claim_id(stance.target_claim_id) not in active_ids
            ):
                continue
            payloads.append(_stance_key_from_charter(stance))
        return sorted(_stance_dependency_key(payload) for payload in payloads)

    return sorted(
        _stance_dependency_key(_stance_key_from_charter(stance))
        for stance in world.stances_between({str(claim_id) for claim_id in active_ids})
    )

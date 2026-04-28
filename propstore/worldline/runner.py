"""Worldline materialization engine."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from propstore.core.activation import claim_lifting_materializations
from propstore.core.id_types import ConceptId, ContextId, to_concept_id
from propstore.core.row_types import coerce_claim_row
from propstore.policies import policy_profile_from_render_policy
from propstore.worldline.argumentation import capture_argumentation_state
from propstore.worldline.definition import WorldlineDefinition, WorldlineResult
from propstore.worldline.hashing import compute_worldline_content_hash
from propstore.worldline.interfaces import HasEnvironment, WorldlineStore
from propstore.worldline.result_types import (
    WorldlineCaptureError,
    WorldlineArgumentationState,
    WorldlineDependencies,
    WorldlineSensitivityEntry,
    WorldlineSensitivityOutcome,
    WorldlineSensitivityReport,
    WorldlineTargetValue,
)
from propstore.worldline.resolution import (
    ResolutionContext,
    concept_name as _concept_name,
    display_claim_id as _display_claim_id,
    pre_resolve_conflicts as _pre_resolve_conflicts,
    resolve_concept_name as _resolve_concept_name,
    resolve_target as _resolve_target,
)
from propstore.worldline.revision_capture import capture_revision_state
from propstore.worldline.revision_types import WorldlineRevisionState
from propstore.worldline.trace import ResolutionTrace

logger = logging.getLogger(__name__)


def run_worldline(
    definition: WorldlineDefinition,
    world: WorldlineStore,
) -> WorldlineResult:
    from propstore.world.types import ResolutionStrategy

    environment = definition.inputs.environment
    bindings = dict(environment.bindings)
    context_id = environment.context_id
    overrides = dict(definition.inputs.overrides)
    policy = definition.policy
    strategy = policy.strategy
    bound = world.bind(environment, policy=policy)

    override_concept_ids: dict[ConceptId, float | str] = {}
    for name, value in overrides.items():
        concept_id = _resolve_concept_name(world, name)
        if concept_id is not None:
            override_concept_ids[concept_id] = value

    trace = ResolutionTrace()
    for key, value in bindings.items():
        trace.record_binding(key, value)
    for name, value in overrides.items():
        trace.record_override(name, value)

    target_map: dict[str, ConceptId] = {}
    for target in definition.targets:
        concept_id = _resolve_concept_name(world, target)
        if concept_id is not None:
            target_map[target] = concept_id

    resolution_context = ResolutionContext(
        query_world=bound,
        world=world,
        override_values=override_concept_ids,
        resolved_values={},
        policy=policy,
    )

    if strategy is not None:
        _pre_resolve_conflicts(resolution_context, target_map, trace)

    values: dict[str, WorldlineTargetValue] = {}
    for target_name, concept_id in target_map.items():
        values[target_name] = _resolve_target(
            resolution_context,
            concept_id,
            target_name,
            trace,
        )

    for target in definition.targets:
        if target not in values:
            values[target] = WorldlineTargetValue(
                status="underspecified",
                reason=f"concept '{target}' not found in knowledge base",
            )

    sensitivity_results = _capture_sensitivity(
        world,
        bound,
        target_map,
        values,
        override_concept_ids,
    )

    argumentation_state: WorldlineArgumentationState | None = None
    stance_dependencies: list[str] = []
    if strategy == ResolutionStrategy.ARGUMENTATION:
        try:
            argumentation_state, stance_dependencies, active_ids = capture_argumentation_state(
                bound,
                world,
                definition,
            )
            if argumentation_state is not None:
                trace.dependency_claims.update(active_ids)
        except Exception as exc:
            logger.warning("argumentation capture failed", exc_info=True)
            argumentation_state = WorldlineArgumentationState(
                status="error",
                error=WorldlineCaptureError.ARGUMENTATION,
            )

    revision_state: WorldlineRevisionState | None = None
    if definition.revision is not None:
        try:
            revision_state = capture_revision_state(bound, definition.revision)
        except Exception as exc:
            logger.warning("revision capture failed", exc_info=True)
            revision_state = WorldlineRevisionState(
                operation=definition.revision.operation,
                status="error",
                error=WorldlineCaptureError.REVISION,
            )

    lifting_rules, blocked_exceptions = _lifting_dependencies(bound, world, context_id)
    dependencies = WorldlineDependencies(
        claims=tuple(sorted(
            _display_claim_id(world, str(claim_id)) or str(claim_id)
            for claim_id in trace.dependency_claims
        )),
        stances=tuple(stance_dependencies),
        contexts=tuple(_context_dependencies(bound, context_id)),
        lifting_rules=tuple(lifting_rules),
        blocked_exceptions=tuple(blocked_exceptions),
    )
    content_hash = compute_worldline_content_hash(
        policy=policy_profile_from_render_policy(definition.policy).to_dict(),
        values=values,
        steps=trace.steps,
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
        revision=revision_state,
    )

    return WorldlineResult(
        computed=datetime.now(timezone.utc).isoformat(),
        content_hash=content_hash,
        values=values,
        steps=tuple(trace.steps),
        dependencies=dependencies,
        sensitivity=sensitivity_results,
        argumentation=argumentation_state,
        revision=revision_state,
    )


def _capture_sensitivity(
    world: WorldlineStore,
    bound: Any,
    target_map: dict[str, ConceptId],
    values: dict[str, WorldlineTargetValue],
    override_concept_ids: dict[ConceptId, float | str],
) -> WorldlineSensitivityReport | None:
    outcomes: dict[str, WorldlineSensitivityOutcome] = {}
    float_overrides = {
        str(concept_id): float(value)
        for concept_id, value in override_concept_ids.items()
        if isinstance(value, (int, float))
    }
    for target_name, concept_id in target_map.items():
        value = values.get(target_name)
        if value is None or value.status != "derived":
            continue
        try:
            from propstore.sensitivity import analyze_sensitivity

            result = analyze_sensitivity(
                world,
                to_concept_id(concept_id),
                bound,
                override_values=float_overrides,
            )
            if result is not None and result.entries:
                outcomes[target_name] = WorldlineSensitivityOutcome(
                    entries=tuple(
                        WorldlineSensitivityEntry(
                            input_name=_concept_name(world, entry.input_concept_id),
                            elasticity=entry.elasticity,
                            partial_derivative=entry.partial_derivative_value,
                        )
                        for entry in result.entries
                        if entry.elasticity is not None
                    )
                )
        except Exception as exc:
            logger.warning("sensitivity analysis failed for %s", target_name, exc_info=True)
            outcomes[target_name] = WorldlineSensitivityOutcome(
                error=WorldlineCaptureError.SENSITIVITY,
            )
    if not outcomes:
        return None
    return WorldlineSensitivityReport(targets=outcomes)


def _context_dependencies(
    bound: Any,
    context_id: ContextId | None,
) -> list[str]:
    if not context_id:
        return []

    dependencies = [str(context_id)]
    if isinstance(bound, HasEnvironment):
        for assumption in bound._environment.effective_assumptions:
            dependencies.append(f"assumption:{assumption}")
    return dependencies


def _lifting_dependencies(
    bound: Any,
    world: WorldlineStore,
    context_id: ContextId | None,
) -> tuple[list[str], list[str]]:
    if context_id is None:
        return [], []

    environment = getattr(bound, "_environment", None)
    lifting_system = getattr(bound, "_lifting_system", None)
    if environment is None or lifting_system is None:
        return [], []

    from propstore.context_lifting import LiftingMaterializationStatus

    rule_ids: set[str] = set()
    blocked_exception_ids: set[str] = set()
    for claim_input in world.claims_for(None):
        claim = coerce_claim_row(claim_input)
        materializations = claim_lifting_materializations(
            claim_context_id=(
                None if claim.context_id is None else str(claim.context_id)
            ),
            claim_id=str(claim.claim_id),
            environment=environment,
            lifting_system=lifting_system,
        )
        for materialization in materializations:
            if materialization.target_context.id != context_id:
                continue
            rule_ids.add(materialization.rule_id)
            if (
                materialization.status is LiftingMaterializationStatus.BLOCKED
                and materialization.exception_id is not None
            ):
                blocked_exception_ids.add(materialization.exception_id)
    return sorted(rule_ids), sorted(blocked_exception_ids)

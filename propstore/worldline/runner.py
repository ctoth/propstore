"""Worldline materialization engine.

``run_worldline`` is the render-time hypothetical: it binds a world over the
corpus, resolves each target, captures argumentation/value/sensitivity/revision
state, and fingerprints the rendered content. It never mutates source. When a
subsystem (sensitivity, argumentation, revision) raises, the runner records an
explicit error indicator rather than fabricating or silently dropping a result.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from propstore.core.id_types import ConceptId, ContextId, to_concept_id
from propstore.policies import policy_profile_from_render_policy
from propstore.worldline.argumentation import capture_argumentation_state
from propstore.worldline.definition import WorldlineDefinition
from propstore.worldline.hashing import compute_worldline_content_hash
from propstore.worldline.interfaces import HasEnvironment, HasLiftingSystem, WorldlineStore
from propstore.worldline.query import WorldlineResult, WorldlineRevisionQuery
from propstore.worldline.result_types import (
    WorldlineArgumentationState,
    WorldlineCaptureError,
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
    from propstore.world.types import RenderPolicy, ResolutionStrategy

    # Compile the charter's stored dict serialization into the canonical compute
    # forms one-way at use time (CLAUDE.md substrate discipline point 3): the
    # charter stays storage-pure, the runner owns the world-shaped types.
    inputs = definition.inputs
    environment = inputs.environment
    bindings = dict(environment.bindings)
    context_id = environment.context_id
    overrides = dict(inputs.overrides)
    policy = RenderPolicy.from_dict(definition.policy)
    revision = WorldlineRevisionQuery.from_dict(definition.revision)
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
                policy,
            )
            if argumentation_state is not None:
                trace.dependency_claims.update(active_ids)
        except Exception:
            logger.warning("argumentation capture failed", exc_info=True)
            argumentation_state = WorldlineArgumentationState(
                status="error",
                error=WorldlineCaptureError.ARGUMENTATION,
            )

    revision_state: WorldlineRevisionState | None = None
    if revision is not None:
        try:
            revision_state = capture_revision_state(bound, revision)
        except Exception:
            logger.warning("revision capture failed", exc_info=True)
            revision_state = WorldlineRevisionState(
                operation=revision.operation,
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
        policy=policy_profile_from_render_policy(policy).to_dict(),
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


def worldline_is_stale(definition: WorldlineDefinition, world: WorldlineStore) -> bool:
    """Whether a worldline's stored result no longer matches a fresh render.

    Lives in the execution layer (not on the storage-pure charter) because it
    re-runs the worldline: a worldline with no stored result is never stale, one
    whose stored ``content_hash`` is empty is always stale, and otherwise the
    current render's content hash is compared against the stored one.
    """

    results = definition.results
    if results is None:
        return False

    stored = WorldlineResult.from_dict(results)
    stored_hash = "" if stored is None else stored.content_hash
    if not stored_hash:
        return True

    return run_worldline(definition, world).content_hash != stored_hash


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
        except Exception:
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
        for assumption in bound.environment.effective_assumptions:
            dependencies.append(f"assumption:{assumption}")
    return dependencies


def _lifting_dependencies(
    bound: Any,
    world: WorldlineStore,
    context_id: ContextId | None,
) -> tuple[list[str], list[str]]:
    if context_id is None:
        return [], []

    if not isinstance(bound, HasEnvironment):
        return [], []
    if not isinstance(bound, HasLiftingSystem) or bound.lifting_system is None:
        return [], []
    environment = bound.environment
    lifting_system = bound.lifting_system

    from propstore.context_lifting import IstProposition, LiftingDecisionStatus

    rule_ids: set[str] = set()
    blocked_exception_ids: set[str] = set()
    for claim in world.claims_for(None):
        if claim.context_id is None or claim.context_id == environment.context_id:
            continue
        decisions = lifting_system.lift_decisions_for(
            IstProposition(
                context=str(claim.context_id),
                proposition_id=str(claim.claim_id),
            )
        )
        for decision in decisions:
            if decision.target_context != str(context_id):
                continue
            rule_ids.add(decision.rule_id)
            if (
                decision.status is LiftingDecisionStatus.EXCEPTED
                and decision.exception_id is not None
            ):
                blocked_exception_ids.add(decision.exception_id)
    return sorted(rule_ids), sorted(blocked_exception_ids)

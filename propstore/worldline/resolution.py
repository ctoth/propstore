from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass

from propstore.core.id_types import ConceptId
from propstore.core.environment import WorldStore
from propstore.families.claims.declaration import Claim
from propstore.world.types import (
    DerivedResult,
    RenderPolicy,
    ResolvedResult,
    ValueResult,
)
from propstore.world.value_resolver import ClaimValueResolver
from propstore.worldline.interfaces import HasEnvironment, WorldlineBoundView
from propstore.worldline.result_types import (
    WorldlineInputSource,
    WorldlineTargetValue,
    WorldlineVariableRef,
)
from propstore.worldline.trace import ResolutionTrace


@dataclass
class ResolutionContext:
    query_world: WorldlineBoundView
    world: WorldStore
    override_values: dict[ConceptId, float | str]
    resolved_values: dict[ConceptId, ResolvedResult]
    policy: RenderPolicy

    def numeric_overrides(self) -> dict[str, float | str | None]:
        numeric_values: dict[str, float | str | None] = {
            str(key): float(value)
            for key, value in self.override_values.items()
            if isinstance(value, (int, float))
        }
        numeric_values.update(
            {
                str(key): float(result.value)
                for key, result in self.resolved_values.items()
                if isinstance(result.value, (int, float))
            }
        )
        return numeric_values


def concept_name(world: WorldStore, concept_id: ConceptId | str) -> str:
    concept = world.get_concept(concept_id)
    return concept.canonical_name if concept else str(concept_id)


def pre_resolve_conflicts(
    context: ResolutionContext,
    target_map: Mapping[str, ConceptId],
    trace: ResolutionTrace,
) -> None:
    from propstore.parameterization_walk import reachable_concepts
    from propstore.world.resolution import resolve

    needs_check = reachable_concepts(
        {str(concept_id) for concept_id in target_map.values()},
        context.world.parameterizations_for,
    )

    for cid in needs_check:
        normalized_cid = ConceptId(cid)
        if normalized_cid in context.override_values:
            continue

        value_result = context.query_world.value_of(normalized_cid)
        if value_result.status != "conflicted":
            continue

        resolved = resolve(
            context.query_world,
            normalized_cid,
            policy=context.policy,
            world=context.world,
        )
        if resolved.status != "resolved" or resolved.value is None:
            continue

        context.resolved_values[normalized_cid] = resolved
        trace.record_claim_dependencies(resolved.claims)
        trace.record_step(
            concept=concept_name(context.world, normalized_cid),
            value=resolved.value,
            source="resolved",
            strategy=resolved.strategy,
            reason=resolved.reason,
            claim_id=resolved.winning_claim_id,
        )


def trace_input_source(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId] | None = None,
) -> WorldlineInputSource:
    if seen is None:
        seen = set()
    if concept_id in seen:
        return WorldlineInputSource(source="cycle")
    seen.add(concept_id)

    try:
        value_result = context.query_world.value_of(concept_id)
        if concept_id in context.override_values:
            return WorldlineInputSource(
                value=context.override_values[concept_id],
                source="override",
            )

        resolved = context.resolved_values.get(concept_id)
        if resolved is not None and resolved.value is not None:
            return WorldlineInputSource(
                value=resolved.value,
                source="resolved",
                claim_id=(
                    ClaimValueResolver.display_claim_id(
                        context.world, resolved.winning_claim_id
                    )
                    or resolved.winning_claim_id
                    if resolved.winning_claim_id
                    else None
                ),
                strategy=resolved.strategy,
                reason=resolved.reason,
            )

        if value_result.status == "determined":
            claim = value_result.claims[0] if value_result.claims else None
            if claim is not None:
                if not isinstance(claim, Claim):
                    raise TypeError(
                        "value_result.claims must contain typed Claim objects"
                    )
                claim_id = str(claim.id)
                trace.record_claim_dependency(claim_id)
                return WorldlineInputSource(
                    value=ClaimValueResolver.claim_value(claim),
                    source="claim",
                    claim_id=ClaimValueResolver.display_claim_id(
                        context.world, claim_id
                    )
                    or claim_id,
                )

        if value_result.status == "conflicted" and context.policy.strategy is not None:
            from propstore.world.resolution import resolve

            resolved = resolve(
                context.query_world,
                concept_id,
                policy=context.policy,
                world=context.world,
            )
            if resolved.status == "resolved" and resolved.value is not None:
                trace.record_claim_dependencies(resolved.claims)
                return WorldlineInputSource(
                    value=resolved.value,
                    source="resolved",
                    claim_id=(
                        ClaimValueResolver.display_claim_id(
                            context.world, resolved.winning_claim_id
                        )
                        or resolved.winning_claim_id
                        if resolved.winning_claim_id
                        else None
                    ),
                    strategy=resolved.strategy,
                    reason=resolved.reason,
                )

        derived = context.query_world.derived_value(
            concept_id,
            override_values=context.numeric_overrides(),
        )
        if derived.status == "derived" and derived.value is not None:
            nested_inputs: dict[str, WorldlineInputSource] = {}
            for input_cid, input_value in derived.input_values.items():
                normalized_input_cid = ConceptId(input_cid)
                input_source = trace_input_source(
                    context,
                    normalized_input_cid,
                    trace,
                    seen,
                )
                nested_inputs[str(normalized_input_cid)] = WorldlineInputSource(
                    source=input_source.source,
                    value=input_value
                    if input_source.value is None
                    else input_source.value,
                    claim_id=input_source.claim_id,
                    formula=input_source.formula,
                    reason=input_source.reason,
                    strategy=input_source.strategy,
                    inputs_used=input_source.inputs_used,
                )

            return WorldlineInputSource(
                value=derived.value,
                source="derived",
                formula=derived.formula,
                inputs_used=nested_inputs,
            )

        return WorldlineInputSource(source="unknown")
    finally:
        seen.discard(concept_id)


def worldline_target_value_from_resolved(
    context: ResolutionContext,
    resolved: ResolvedResult,
) -> WorldlineTargetValue:
    return WorldlineTargetValue(
        status="resolved",
        value=resolved.value,
        source="resolved",
        winning_claim_id=(
            ClaimValueResolver.display_claim_id(
                context.world, resolved.winning_claim_id
            )
            if resolved.winning_claim_id
            else None
        ),
        strategy=resolved.strategy,
        reason=resolved.reason,
    )

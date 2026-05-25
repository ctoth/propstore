from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass

from propstore.core.id_types import ConceptId
from propstore.core.environment import WorldStore
from propstore.families.claims.declaration import Claim
from propstore.world.types import DerivedResult, RenderPolicy, ResolvedResult, ValueResult
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
    return (
        concept.canonical_name
        if concept
        else str(concept_id)
    )


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


def resolve_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
) -> WorldlineTargetValue:
    value_result = context.query_world.value_of(concept_id)

    if concept_id in context.override_values:
        return WorldlineTargetValue(
            status="determined",
            value=context.override_values[concept_id],
            source="override",
        )

    resolved = context.resolved_values.get(concept_id)
    if resolved is not None and resolved.value is not None:
        return worldline_target_value_from_resolved(context, resolved)

    if value_result.status == "determined":
        claim = value_result.claims[0] if value_result.claims else None
        if claim is not None:
            if not isinstance(claim, Claim):
                raise TypeError("value_result.claims must contain typed Claim objects")
            claim_id = str(claim.id)
            trace.record_claim_dependency(claim_id)
            display_id = ClaimValueResolver.display_claim_id(context.world, claim_id) or claim_id
            payload = ClaimValueResolver.claim_payload(claim)
            target_value = WorldlineTargetValue(
                status="determined",
                source="claim",
                claim_id=display_id,
                value=payload.value,
                claim_type=payload.claim_type.value,
                statement=payload.statement,
                expression=payload.expression,
                name=payload.name,
                body=payload.body,
                canonical_ast=payload.canonical_ast,
                variables=tuple(
                    WorldlineVariableRef(
                        name=variable.name,
                        symbol=variable.symbol,
                        concept_id=variable.concept_id,
                    )
                    for variable in payload.variables
                ),
            )
            trace.record_step(
                concept=target_name,
                source="claim",
                value=target_value.value,
                claim_id=target_value.claim_id,
            )
            return target_value

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
            trace.record_step(
                concept=target_name,
                value=resolved.value,
                source="resolved",
                strategy=resolved.strategy,
                reason=resolved.reason,
            )
            return worldline_target_value_from_resolved(context, resolved)

    derived = context.query_world.derived_value(
        concept_id,
        override_values=context.numeric_overrides(),
    )
    if derived.status == "derived" and derived.value is not None:
        inputs_used: dict[str, WorldlineInputSource] = {}
        for input_cid, input_value in derived.input_values.items():
            normalized_input_cid = ConceptId(input_cid)
            input_source = trace_input_source(
                context,
                normalized_input_cid,
                trace,
            )
            inputs_used[str(normalized_input_cid)] = WorldlineInputSource(
                source=input_source.source,
                value=input_value if input_source.value is None else input_source.value,
                claim_id=input_source.claim_id,
                formula=input_source.formula,
                reason=input_source.reason,
                strategy=input_source.strategy,
                inputs_used=input_source.inputs_used,
            )
        seen_concepts = trace.seen_concepts()
        for input_cid, input_info in inputs_used.items():
            input_name = concept_name(context.world, input_cid)
            if input_name in seen_concepts:
                continue
            trace.record_step(
                concept=input_name,
                value=input_info.value,
                source=input_info.source,
                claim_id=input_info.claim_id,
                strategy=input_info.strategy,
                reason=input_info.reason,
                formula=input_info.formula,
            )

        trace.record_step(
            concept=target_name,
            value=derived.value,
            source="derived",
            formula=derived.formula,
        )
        return WorldlineTargetValue(
            status="derived",
            value=derived.value,
            source="derived",
            formula=derived.formula,
            inputs_used=inputs_used,
        )

    strategy_enum = context.policy.strategy if context.policy.strategy is not None else None
    chain_bindings: dict[str, object] = {}
    if isinstance(context.query_world, HasEnvironment):
        chain_bindings = dict(context.query_world.environment.bindings)
    try:
        chain_result = context.world.chain_query(
            concept_id,
            strategy=strategy_enum,
            **chain_bindings,
        )
    except Exception as exc:
        reason = f"chain query failed: {exc}"
        trace.record_step(
            concept=target_name,
            value=None,
            source="error",
            reason=reason,
        )
        return WorldlineTargetValue(
            status="error",
            reason=reason,
        )

    result = chain_result.result
    chain_value: float | str | None
    formula: str | None = None
    input_values: dict[ConceptId, float] = {}
    if isinstance(result, DerivedResult):
        chain_value = result.value
        formula = result.formula
        input_values = {
            ConceptId(input_cid): value
            for input_cid, value in result.input_values.items()
        }
    elif isinstance(result, ValueResult):
        chain_value = ClaimValueResolver.value_result_claim_value(result)
    else:
        raise TypeError("chain_result.result must be ValueResult or DerivedResult")

    if chain_value is not None and result.status in ("derived", "determined"):
        for chain_step in chain_result.steps:
            if chain_step.source == "claim":
                step_result = context.query_world.value_of(chain_step.concept_id)
                if step_result.claims:
                    trace.record_claim_dependency(str(step_result.claims[0].id))

        for chain_step in chain_result.steps:
            if chain_step.concept_id == concept_id or chain_step.source == "binding":
                continue
            trace.record_step(
                concept=concept_name(context.world, chain_step.concept_id),
                value=chain_step.value,
                source=chain_step.source,
            )

        trace.record_step(
            concept=target_name,
            value=chain_value,
            source="derived",
            formula=formula,
        )

        inputs_used: dict[str, WorldlineInputSource] = {}
        for input_cid, input_value in input_values.items():
            input_source = trace_input_source(context, input_cid, trace)
            inputs_used[str(input_cid)] = WorldlineInputSource(
                source=input_source.source,
                value=input_value if input_source.value is None else input_source.value,
                claim_id=input_source.claim_id,
                formula=input_source.formula,
                reason=input_source.reason,
                strategy=input_source.strategy,
                inputs_used=input_source.inputs_used,
            )
        return WorldlineTargetValue(
            status="derived",
            value=chain_value,
            source="derived",
            formula=formula,
            inputs_used=inputs_used,
        )

    reason = f"status={value_result.status}"
    if value_result.status == "no_claims":
        reason = "no claims and no override provided"
    elif value_result.status == "no_values":
        reason = "claims exist but none have scalar values"
    elif value_result.status == "conflicted":
        reason = "conflicted with no resolution strategy"
    elif value_result.status == "underdetermined":
        reason = "underdetermined"

    trace.record_step(
        concept=target_name,
        value=None,
        source="underspecified",
        reason=reason,
    )
    return WorldlineTargetValue(
        status="underspecified",
        reason=reason,
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
                    ClaimValueResolver.display_claim_id(context.world, resolved.winning_claim_id)
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
                    raise TypeError("value_result.claims must contain typed Claim objects")
                claim_id = str(claim.id)
                trace.record_claim_dependency(claim_id)
                return WorldlineInputSource(
                    value=ClaimValueResolver.claim_value(claim),
                    source="claim",
                    claim_id=ClaimValueResolver.display_claim_id(context.world, claim_id) or claim_id,
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
                        ClaimValueResolver.display_claim_id(context.world, resolved.winning_claim_id)
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
                    value=input_value if input_source.value is None else input_source.value,
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
            ClaimValueResolver.display_claim_id(context.world, resolved.winning_claim_id)
            if resolved.winning_claim_id
            else None
        ),
        strategy=resolved.strategy,
        reason=resolved.reason,
    )

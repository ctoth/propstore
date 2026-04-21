from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from propstore.core.active_claims import ActiveClaim
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.core.environment import WorldStore
from propstore.core.row_types import coerce_claim_row, coerce_concept_row
from propstore.world.types import DerivedResult, RenderPolicy, ResolvedResult
from propstore.worldline.interfaces import HasBindings, WorldlineBoundView
from propstore.worldline.result_types import WorldlineInputSource, WorldlineTargetValue
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
    return coerce_concept_row(concept).canonical_name if concept else str(concept_id)


def resolve_concept_name(world: WorldStore, name: str) -> ConceptId | None:
    resolved = world.resolve_concept(name)
    return None if resolved is None else to_concept_id(resolved)


def display_claim_id(world: WorldStore, claim_id: str | None) -> str | None:
    if claim_id is None:
        return None
    claim = world.get_claim(claim_id)
    if claim is not None:
        row = coerce_claim_row(claim)
        logical_value = row.primary_logical_value
        if isinstance(logical_value, str) and logical_value:
            return logical_value
    return claim_id


def claim_target_value(
    *,
    status: str,
    source: str,
    claim: ActiveClaim,
    claim_id: str | None,
) -> WorldlineTargetValue:
    return WorldlineTargetValue.from_mapping({
        "status": status,
        "source": source,
        "claim_id": claim_id,
        "value": claim.value,
        "claim_type": claim.claim_type,
        "statement": claim.statement,
        "expression": claim.expression,
        "body": claim.body,
        "name": claim.name,
        "canonical_ast": claim.canonical_ast,
        "variables": claim.variable_payload(),
    })


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
        normalized_cid = to_concept_id(cid)
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

    for resolver in (
        _resolve_override_target,
        _resolve_preresolved_target,
        _resolve_claim_target,
        _resolve_conflict_target,
        _resolve_derived_target,
        _resolve_chain_target,
    ):
        result = resolver(context, concept_id, target_name, trace, value_result)
        if result is not None:
            return result

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
        for resolver in (
            _resolve_override_input,
            _resolve_preresolved_input,
            _resolve_claim_input,
            _resolve_conflict_input,
            _resolve_derived_input,
        ):
            result = resolver(context, concept_id, trace, seen, value_result)
            if result is not None:
                return result
        return WorldlineInputSource(source="unknown")
    finally:
        seen.discard(concept_id)


def _resolve_override_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    del target_name, trace, value_result
    if concept_id not in context.override_values:
        return None
    return WorldlineTargetValue(
        status="determined",
        value=context.override_values[concept_id],
        source="override",
    )


def _resolved_worldline_target_value(
    context: ResolutionContext,
    resolved: ResolvedResult,
) -> WorldlineTargetValue:
    return WorldlineTargetValue(
        status="resolved",
        value=resolved.value,
        source="resolved",
        winning_claim_id=(
            display_claim_id(context.world, resolved.winning_claim_id)
            if resolved.winning_claim_id
            else None
        ),
        strategy=resolved.strategy,
        reason=resolved.reason,
    )


def _resolve_preresolved_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    del target_name, trace, value_result
    resolved = context.resolved_values.get(concept_id)
    if resolved is None or resolved.value is None:
        return None
    return _resolved_worldline_target_value(context, resolved)


def _resolve_claim_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    del concept_id
    if value_result.status != "determined":
        return None

    claim = value_result.claims[0] if value_result.claims else None
    if claim is None:
        return None
    claim_id = str(claim.claim_id)
    trace.record_claim_dependency(claim_id)
    display_id = display_claim_id(context.world, claim_id) or claim_id
    target_value = claim_target_value(
        status="determined",
        source="claim",
        claim=claim,
        claim_id=display_id,
    )
    trace.record_step(
        concept=target_name,
        source="claim",
        value=target_value.value,
        claim_id=target_value.claim_id,
    )
    return target_value


def _resolve_conflict_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    from propstore.world.resolution import resolve

    if value_result.status != "conflicted" or context.policy.strategy is None:
        return None

    resolved = resolve(
        context.query_world,
        concept_id,
        policy=context.policy,
        world=context.world,
    )
    if resolved.status != "resolved" or resolved.value is None:
        return None

    trace.record_claim_dependencies(resolved.claims)
    trace.record_step(
        concept=target_name,
        value=resolved.value,
        source="resolved",
        strategy=resolved.strategy,
        reason=resolved.reason,
    )
    return _resolved_worldline_target_value(context, resolved)


def _resolve_derived_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    del value_result
    derived = context.query_world.derived_value(
        concept_id,
        override_values=context.numeric_overrides(),
    )
    if derived.status != "derived" or derived.value is None:
        return None

    inputs_used = _trace_derived_inputs(context, derived, trace)
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


def _resolve_chain_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> WorldlineTargetValue | None:
    del value_result
    strategy_enum = context.policy.strategy if context.policy.strategy is not None else None
    chain_bindings: dict[str, Any] = {}
    if isinstance(context.query_world, HasBindings):
        chain_bindings = dict(context.query_world._bindings)
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
            to_concept_id(input_cid): value
            for input_cid, value in result.input_values.items()
        }
    else:
        chain_value = result.claims[0].value if result.claims else None

    if chain_value is None or result.status not in ("derived", "determined"):
        return None

    for chain_step in chain_result.steps:
        if chain_step.source == "claim":
            step_result = context.query_world.value_of(chain_step.concept_id)
            if step_result.claims:
                trace.record_claim_dependency(str(step_result.claims[0].claim_id))

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


def _resolve_override_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> WorldlineInputSource | None:
    del trace, seen, value_result
    if concept_id not in context.override_values:
        return None
    return WorldlineInputSource(
        value=context.override_values[concept_id],
        source="override",
    )


def _resolve_preresolved_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> WorldlineInputSource | None:
    del trace, seen, value_result
    resolved = context.resolved_values.get(concept_id)
    if resolved is None or resolved.value is None:
        return None
    return WorldlineInputSource(
        value=resolved.value,
        source="resolved",
        claim_id=(
            display_claim_id(context.world, resolved.winning_claim_id)
            or resolved.winning_claim_id
            if resolved.winning_claim_id
            else None
        ),
        strategy=resolved.strategy,
        reason=resolved.reason,
    )


def _resolve_claim_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> WorldlineInputSource | None:
    del concept_id, seen
    if value_result.status != "determined":
        return None
    claim = value_result.claims[0] if value_result.claims else None
    if claim is None:
        return None
    claim_id = str(claim.claim_id)
    trace.record_claim_dependency(claim_id)
    return WorldlineInputSource(
        value=claim.value,
        source="claim",
        claim_id=display_claim_id(context.world, claim_id) or claim_id,
    )


def _resolve_conflict_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> WorldlineInputSource | None:
    from propstore.world.resolution import resolve

    del seen
    if value_result.status != "conflicted" or context.policy.strategy is None:
        return None

    resolved = resolve(
        context.query_world,
        concept_id,
        policy=context.policy,
        world=context.world,
    )
    if resolved.status != "resolved" or resolved.value is None:
        return None

    trace.record_claim_dependencies(resolved.claims)
    return WorldlineInputSource(
        value=resolved.value,
        source="resolved",
        claim_id=(
            display_claim_id(context.world, resolved.winning_claim_id)
            or resolved.winning_claim_id
            if resolved.winning_claim_id
            else None
        ),
        strategy=resolved.strategy,
        reason=resolved.reason,
    )


def _resolve_derived_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> WorldlineInputSource | None:
    del value_result
    derived = context.query_world.derived_value(
        concept_id,
        override_values=context.numeric_overrides(),
    )
    if derived.status != "derived" or derived.value is None:
        return None

    nested_inputs: dict[str, WorldlineInputSource] = {}
    for input_cid, input_value in derived.input_values.items():
        normalized_input_cid = to_concept_id(input_cid)
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


def _trace_derived_inputs(
    context: ResolutionContext,
    derived: Any,
    trace: ResolutionTrace,
) -> dict[str, WorldlineInputSource]:
    inputs_used: dict[str, WorldlineInputSource] = {}
    for input_cid, input_value in derived.input_values.items():
        normalized_input_cid = to_concept_id(input_cid)
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
    return inputs_used

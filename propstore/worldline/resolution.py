from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from propstore.core.id_types import ConceptId, to_concept_id
from propstore.core.environment import ArtifactStore, ParameterizationLookupStore
from propstore.core.row_types import coerce_claim_row, coerce_concept_row
from propstore.world.types import DerivedResult, RenderPolicy
from propstore.worldline.interfaces import HasBindings, WorldlineBoundView
from propstore.worldline.trace import ResolutionTrace


@dataclass
class ResolutionContext:
    query_world: WorldlineBoundView
    world: ArtifactStore
    override_values: dict[ConceptId, float | str]
    policy: RenderPolicy

    def numeric_overrides(self) -> dict[str, float | str | None]:
        return {
            str(key): float(value)
            for key, value in self.override_values.items()
            if isinstance(value, (int, float))
        }


def concept_name(world: ArtifactStore, concept_id: ConceptId | str) -> str:
    concept = world.get_concept(concept_id)
    return coerce_concept_row(concept).canonical_name if concept else str(concept_id)


def resolve_concept_name(world: ArtifactStore, name: str) -> ConceptId | None:
    resolved = world.resolve_concept(name)
    return None if resolved is None else to_concept_id(resolved)


def display_claim_id(world: ArtifactStore, claim_id: str | None) -> str | None:
    if claim_id is None:
        return None
    getter = getattr(world, "get_claim", None)
    if callable(getter):
        claim = getter(claim_id)
        if claim is not None:
            row = coerce_claim_row(claim)
            logical_value = row.primary_logical_value
            if isinstance(logical_value, str) and logical_value:
                return logical_value
    return claim_id


def claim_payload(claim: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    value = claim.get("value")
    if value is not None:
        payload["value"] = value

    claim_type = claim.get("type")
    if claim_type:
        payload["claim_type"] = claim_type

    for field in ("statement", "expression", "body", "name", "canonical_ast"):
        field_value = claim.get(field)
        if field_value:
            payload[field] = field_value

    variables_json = claim.get("variables_json")
    if variables_json:
        try:
            payload["variables"] = json.loads(variables_json)
        except (TypeError, json.JSONDecodeError):
            payload["variables"] = variables_json

    return payload


def pre_resolve_conflicts(
    context: ResolutionContext,
    target_map: Mapping[str, ConceptId],
    trace: ResolutionTrace,
) -> None:
    from propstore.parameterization_walk import reachable_concepts
    from propstore.world import resolve

    parameterizations_for = (
        context.world.parameterizations_for
        if isinstance(context.world, ParameterizationLookupStore)
        else (lambda _concept_id: [])
    )
    needs_check = reachable_concepts(
        {str(concept_id) for concept_id in target_map.values()},
        parameterizations_for,
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

        context.override_values[normalized_cid] = resolved.value
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
) -> dict[str, Any]:
    value_result = context.query_world.value_of(concept_id)

    for resolver in (
        _resolve_override_target,
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
    return {
        "status": "underspecified",
        "reason": reason,
    }


def trace_input_source(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId] | None = None,
) -> dict[str, Any]:
    if seen is None:
        seen = set()
    if concept_id in seen:
        return {"source": "cycle"}
    seen.add(concept_id)

    try:
        value_result = context.query_world.value_of(concept_id)
        for resolver in (
            _resolve_override_input,
            _resolve_claim_input,
            _resolve_conflict_input,
            _resolve_derived_input,
        ):
            result = resolver(context, concept_id, trace, seen, value_result)
            if result is not None:
                return result
        return {"source": "unknown"}
    finally:
        seen.discard(concept_id)


def _resolve_override_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> dict[str, Any] | None:
    del target_name, trace, value_result
    if concept_id not in context.override_values:
        return None
    return {
        "status": "determined",
        "value": context.override_values[concept_id],
        "source": "override",
    }


def _resolve_claim_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> dict[str, Any] | None:
    del concept_id
    if value_result.status != "determined":
        return None

    claim = value_result.claims[0] if value_result.claims else {}
    claim_id = claim.get("id")
    if isinstance(claim_id, str):
        trace.record_claim_dependency(claim_id)
    payload = claim_payload(claim)
    step = {"concept": target_name, "source": "claim"}
    step.update(payload)
    if claim_id:
        step["claim_id"] = display_claim_id(context.world, claim_id) or claim_id
    trace.record_step(**step)

    result = {
        "status": "determined",
        "source": "claim",
        "claim_id": display_claim_id(context.world, claim_id) if claim_id else None,
    }
    result.update(payload)
    return result


def _resolve_conflict_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> dict[str, Any] | None:
    from propstore.world import resolve

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
    return {
        "status": "resolved",
        "value": resolved.value,
        "source": "resolved",
        "winning_claim_id": (
            display_claim_id(context.world, resolved.winning_claim_id)
            if resolved.winning_claim_id
            else None
        ),
        "strategy": resolved.strategy,
        "reason": resolved.reason,
    }


def _resolve_derived_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> dict[str, Any] | None:
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
        step: dict[str, Any] = {
            "concept": input_name,
            "value": input_info.get("value"),
            "source": input_info.get("source", "unknown"),
        }
        if input_info.get("claim_id"):
            step["claim_id"] = input_info["claim_id"]
        if input_info.get("formula"):
            step["formula"] = input_info["formula"]
        trace.record_step(**step)

    trace.record_step(
        concept=target_name,
        value=derived.value,
        source="derived",
        formula=derived.formula,
    )
    return {
        "status": "derived",
        "value": derived.value,
        "source": "derived",
        "formula": derived.formula,
        "inputs_used": inputs_used,
    }


def _resolve_chain_target(
    context: ResolutionContext,
    concept_id: ConceptId,
    target_name: str,
    trace: ResolutionTrace,
    value_result: Any,
) -> dict[str, Any] | None:
    del value_result
    strategy_enum = context.policy.strategy if context.policy.strategy is not None else None
    chain_bindings = (
        dict(context.query_world._bindings)
        if isinstance(context.query_world, HasBindings)
        else {}
    )
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
        return {
            "status": "error",
            "reason": reason,
        }

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
        chain_value = result.claims[0].get("value") if result.claims else None

    if chain_value is None or result.status not in ("derived", "determined"):
        return None

    for chain_step in chain_result.steps:
        if chain_step.source == "claim":
            step_result = context.query_world.value_of(chain_step.concept_id)
            if step_result.claims:
                dependency_id = step_result.claims[0].get("id")
                if isinstance(dependency_id, str):
                    trace.record_claim_dependency(dependency_id)

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

    inputs_used: dict[ConceptId, dict[str, Any]] = {}
    for input_cid, input_value in input_values.items():
        inputs_used[input_cid] = trace_input_source(context, input_cid, trace)
        inputs_used[input_cid].setdefault("value", input_value)
    return {
        "status": "derived",
        "value": chain_value,
        "source": "derived",
        "formula": formula,
        "inputs_used": inputs_used,
    }


def _resolve_override_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> dict[str, Any] | None:
    del trace, seen, value_result
    if concept_id not in context.override_values:
        return None
    return {
        "value": context.override_values[concept_id],
        "source": "override",
    }


def _resolve_claim_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> dict[str, Any] | None:
    del concept_id, seen
    if value_result.status != "determined":
        return None
    claim = value_result.claims[0] if value_result.claims else {}
    claim_id = claim.get("id")
    if isinstance(claim_id, str):
        trace.record_claim_dependency(claim_id)
    result = {
        "value": claim.get("value"),
        "source": "claim",
    }
    if claim_id:
        result["claim_id"] = display_claim_id(context.world, claim_id) or claim_id
    return result


def _resolve_conflict_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> dict[str, Any] | None:
    from propstore.world import resolve

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
    result = {
        "value": resolved.value,
        "source": "resolved",
        "strategy": resolved.strategy,
    }
    if resolved.winning_claim_id:
        result["claim_id"] = (
            display_claim_id(context.world, resolved.winning_claim_id)
            or resolved.winning_claim_id
        )
    if resolved.reason:
        result["reason"] = resolved.reason
    return result


def _resolve_derived_input(
    context: ResolutionContext,
    concept_id: ConceptId,
    trace: ResolutionTrace,
    seen: set[ConceptId],
    value_result: Any,
) -> dict[str, Any] | None:
    del value_result
    derived = context.query_world.derived_value(
        concept_id,
        override_values=context.numeric_overrides(),
    )
    if derived.status != "derived" or derived.value is None:
        return None

    nested_inputs: dict[ConceptId, dict[str, Any]] = {}
    for input_cid, input_value in derived.input_values.items():
        normalized_input_cid = to_concept_id(input_cid)
        nested_inputs[normalized_input_cid] = trace_input_source(
            context,
            normalized_input_cid,
            trace,
            seen,
        )
        nested_inputs[normalized_input_cid].setdefault("value", input_value)

    result: dict[str, Any] = {
        "value": derived.value,
        "source": "derived",
    }
    if derived.formula:
        result["formula"] = derived.formula
    if nested_inputs:
        result["inputs_used"] = nested_inputs
    return result


def _trace_derived_inputs(
    context: ResolutionContext,
    derived: Any,
    trace: ResolutionTrace,
) -> dict[ConceptId, dict[str, Any]]:
    inputs_used: dict[ConceptId, dict[str, Any]] = {}
    for input_cid, input_value in derived.input_values.items():
        normalized_input_cid = to_concept_id(input_cid)
        inputs_used[normalized_input_cid] = trace_input_source(
            context,
            normalized_input_cid,
            trace,
        )
        inputs_used[normalized_input_cid].setdefault("value", input_value)
    return inputs_used

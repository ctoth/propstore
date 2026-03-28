"""Graph-native activation over compiled semantic graphs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.environment import Environment
from propstore.core.labels import binding_condition_to_cel

if TYPE_CHECKING:
    from propstore.validate_contexts import ContextHierarchy
    from propstore.z3_conditions import Z3ConditionSolver


def _binding_conditions(environment: Environment) -> tuple[str, ...]:
    conditions = [
        binding_condition_to_cel(key, value)
        for key, value in sorted(environment.bindings.items())
    ]
    for assumption in environment.effective_assumptions:
        if assumption not in conditions:
            conditions.append(assumption)
    return tuple(conditions)


def _visible_contexts(
    environment: Environment,
    context_hierarchy: ContextHierarchy | None,
) -> set[str] | None:
    if environment.context_id is None or context_hierarchy is None:
        return None
    visible = {environment.context_id}
    visible.update(context_hierarchy.ancestors(environment.context_id))
    return visible


def _claim_attributes(claim: ClaimNode) -> dict[str, Any]:
    return dict(claim.attributes)


def _claim_context_id(claim: ClaimNode) -> str | None:
    context_id = _claim_attributes(claim).get("context_id")
    return None if context_id is None else str(context_id)


def _claim_conditions(claim: ClaimNode) -> tuple[str, ...]:
    raw = _claim_attributes(claim).get("conditions_cel")
    if not raw:
        return ()
    if isinstance(raw, str):
        loaded = json.loads(raw)
        if not loaded:
            return ()
        return tuple(str(item) for item in loaded)
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    return (str(raw),)


def is_claim_node_active(
    claim: ClaimNode,
    *,
    environment: Environment,
    solver: Z3ConditionSolver | None,
    context_hierarchy: ContextHierarchy | None = None,
) -> bool:
    visible_contexts = _visible_contexts(environment, context_hierarchy)
    claim_context_id = _claim_context_id(claim)
    if visible_contexts is not None and claim_context_id is not None:
        if claim_context_id not in visible_contexts:
            return False

    claim_conditions = _claim_conditions(claim)
    if not claim_conditions:
        return True

    binding_conditions = _binding_conditions(environment)
    if not binding_conditions:
        return True
    if solver is None:
        raise ValueError("A condition solver is required for conditional activation")

    return not solver.are_disjoint(binding_conditions, claim_conditions)


def is_claim_mapping_active(
    claim: Mapping[str, Any],
    *,
    environment: Environment,
    solver: Z3ConditionSolver | None,
    context_hierarchy: ContextHierarchy | None = None,
) -> bool:
    visible_contexts = _visible_contexts(environment, context_hierarchy)
    claim_context_id = claim.get("context_id")
    if visible_contexts is not None and claim_context_id is not None:
        if str(claim_context_id) not in visible_contexts:
            return False

    raw_conditions = claim.get("conditions_cel")
    if not raw_conditions:
        return True

    if isinstance(raw_conditions, str):
        claim_conditions = json.loads(raw_conditions)
    elif isinstance(raw_conditions, (list, tuple)):
        claim_conditions = list(raw_conditions)
    else:
        claim_conditions = [raw_conditions]
    if not claim_conditions:
        return True

    binding_conditions = _binding_conditions(environment)
    if not binding_conditions:
        return True
    if solver is None:
        raise ValueError("A condition solver is required for conditional activation")

    return not solver.are_disjoint(binding_conditions, claim_conditions)


def activate_compiled_world_graph(
    compiled: CompiledWorldGraph,
    *,
    environment: Environment,
    solver: Z3ConditionSolver,
    context_hierarchy: ContextHierarchy | None = None,
) -> ActiveWorldGraph:
    active_claim_ids: list[str] = []
    inactive_claim_ids: list[str] = []

    for claim in compiled.claims:
        if is_claim_node_active(
            claim,
            environment=environment,
            solver=solver,
            context_hierarchy=context_hierarchy,
        ):
            active_claim_ids.append(claim.claim_id)
        else:
            inactive_claim_ids.append(claim.claim_id)

    return ActiveWorldGraph(
        compiled=compiled,
        environment=environment,
        active_claim_ids=tuple(active_claim_ids),
        inactive_claim_ids=tuple(inactive_claim_ids),
    )

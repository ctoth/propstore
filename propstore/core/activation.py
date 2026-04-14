"""Graph-native activation over compiled semantic graphs."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from propstore.core.active_claims import ActiveClaim
from propstore.cel_checker import (
    synthetic_category_concept,
    with_standard_synthetic_bindings,
    with_synthetic_concepts,
)
from propstore.core.id_types import ClaimId
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.environment import Environment
from propstore.core.labels import binding_condition_to_cel
from propstore.z3_conditions import Z3TranslationError

if TYPE_CHECKING:
    from propstore.context_hierarchy import ContextHierarchy
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
    visible = {str(environment.context_id)}
    visible.update(str(context_id) for context_id in context_hierarchy.ancestors(str(environment.context_id)))
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


_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NON_BINDING_NAMES = frozenset({"true", "false", "in"})


def _synthetic_names_from_conditions(*condition_groups: tuple[str, ...] | list[str]) -> list[str]:
    names: set[str] = set()
    for group in condition_groups:
        for condition in group:
            for match in _NAME_PATTERN.findall(str(condition)):
                if match not in _NON_BINDING_NAMES:
                    names.add(match)
    return sorted(names)


def _retry_with_standard_bindings(
    solver: Z3ConditionSolver,
    *,
    binding_conditions: tuple[str, ...] | list[str],
    claim_conditions: tuple[str, ...] | list[str],
) -> Z3ConditionSolver:
    try:
        base_registry = getattr(solver, "_registry")
    except AttributeError:
        return solver

    from propstore.z3_conditions import Z3ConditionSolver

    augmented_registry = with_standard_synthetic_bindings(base_registry)
    extra_names = [
        name
        for name in _synthetic_names_from_conditions(binding_conditions, claim_conditions)
        if name not in augmented_registry
    ]
    if extra_names:
        augmented_registry = with_synthetic_concepts(
            augmented_registry,
            [
                synthetic_category_concept(
                    concept_id=f"ps:concept:__{name}__",
                    canonical_name=name,
                    values=(),
                    extensible=True,
                )
                for name in extra_names
            ],
        )
    if augmented_registry == dict(base_registry):
        return solver
    return Z3ConditionSolver(augmented_registry)


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

    try:
        return not solver.are_disjoint(binding_conditions, claim_conditions)
    except Z3TranslationError:
        return not _retry_with_standard_bindings(
            solver,
            binding_conditions=binding_conditions,
            claim_conditions=claim_conditions,
        ).are_disjoint(
            binding_conditions,
            claim_conditions,
        )


def is_active_claim_active(
    claim: ActiveClaim,
    *,
    environment: Environment,
    solver: Z3ConditionSolver | None,
    context_hierarchy: ContextHierarchy | None = None,
) -> bool:
    visible_contexts = _visible_contexts(environment, context_hierarchy)
    claim_context_id = claim.context_id
    if visible_contexts is not None and claim_context_id is not None:
        if str(claim_context_id) not in visible_contexts:
            return False

    claim_conditions = claim.conditions
    if not claim_conditions:
        return True

    binding_conditions = _binding_conditions(environment)
    if not binding_conditions:
        return True
    if solver is None:
        raise ValueError("A condition solver is required for conditional activation")

    try:
        return not solver.are_disjoint(binding_conditions, claim_conditions)
    except Z3TranslationError:
        return not _retry_with_standard_bindings(
            solver,
            binding_conditions=binding_conditions,
            claim_conditions=claim_conditions,
        ).are_disjoint(
            binding_conditions,
            claim_conditions,
        )


def activate_compiled_world_graph(
    compiled: CompiledWorldGraph,
    *,
    environment: Environment,
    solver: Z3ConditionSolver,
    context_hierarchy: ContextHierarchy | None = None,
) -> ActiveWorldGraph:
    active_claim_ids: list[ClaimId] = []
    inactive_claim_ids: list[ClaimId] = []

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

"""Graph-native activation over compiled semantic graphs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from propstore.core.active_claims import ActiveClaim
from propstore.cel_types import CelExpr, to_cel_exprs
from cel_parser import (
    Call,
    CreateList,
    Expr,
    Ident,
    ParseError,
    parse as parse_cel,
)
from propstore.cel_checker import with_standard_synthetic_bindings
from propstore.core.id_types import ClaimId
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.environment import Environment
from propstore.core.labels import binding_condition_to_cel
from propstore.z3_conditions import Z3TranslationError

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem
    from propstore.z3_conditions import Z3ConditionSolver


def _binding_conditions(environment: Environment) -> tuple[CelExpr, ...]:
    conditions = [
        binding_condition_to_cel(key, value)
        for key, value in sorted(environment.bindings.items())
    ]
    for assumption in environment.effective_assumptions:
        if assumption not in conditions:
            conditions.append(assumption)
    return to_cel_exprs(conditions)


def _claim_projected_into_environment(
    *,
    claim_context_id: str | None,
    claim_id: str,
    environment: Environment,
    lifting_system: LiftingSystem | None,
) -> bool:
    if environment.context_id is None or lifting_system is None:
        return True
    if claim_context_id is None:
        return True
    if claim_context_id == str(environment.context_id):
        return True

    from propstore.context_lifting import LiftingDecisionStatus

    materializations = claim_lifting_materializations(
        claim_context_id=claim_context_id,
        claim_id=claim_id,
        environment=environment,
        lifting_system=lifting_system,
    )
    return any(
        materialization.target_context.id == environment.context_id
        and materialization.status is LiftingDecisionStatus.LIFTED
        for materialization in materializations
    )


def claim_lifting_materializations(
    *,
    claim_context_id: str | None,
    claim_id: str,
    environment: Environment,
    lifting_system: LiftingSystem | None,
):
    if environment.context_id is None or lifting_system is None:
        return ()
    if claim_context_id is None:
        return ()
    if claim_context_id == str(environment.context_id):
        return ()

    from propstore.context_lifting import (
        IstProposition,
    )
    from propstore.core.assertions import ContextReference

    return lifting_system.materialize_lifted_assertions(
        (
            IstProposition(
                context=ContextReference(claim_context_id),
                proposition_id=claim_id,
            ),
        )
    )


def _claim_attributes(claim: ClaimNode) -> dict[str, Any]:
    return dict(claim.attributes)


def _claim_context_id(claim: ClaimNode) -> str | None:
    context_id = _claim_attributes(claim).get("context_id")
    return None if context_id is None else str(context_id)


def _claim_conditions(claim: ClaimNode) -> tuple[CelExpr, ...]:
    raw = _claim_attributes(claim).get("conditions_cel")
    if not raw:
        return ()
    if isinstance(raw, str):
        loaded = json.loads(raw)
        if not loaded:
            return ()
        return to_cel_exprs(str(item) for item in loaded)
    if isinstance(raw, (list, tuple)):
        return to_cel_exprs(str(item) for item in raw)
    return to_cel_exprs((str(raw),))


def _claim_node_source_artifact(claim: ClaimNode) -> str | None:
    if claim.provenance is not None and claim.provenance.source_id is not None:
        return claim.provenance.source_id
    return claim.claim_id


_NON_BINDING_NAMES = frozenset({"true", "false", "in"})


class UnknownConceptInCEL(ValueError):
    """Raised when activation sees a CEL identifier outside the registry."""

    def __init__(self, concept_name: str, *, source_artifact: str | None) -> None:
        self.concept_name = concept_name
        self.source_artifact = source_artifact
        context = (
            "without source artifact context"
            if source_artifact is None
            else f"in source artifact {source_artifact}"
        )
        super().__init__(f"Unknown CEL concept '{concept_name}' {context}")


def _names_from_ast(node: Expr) -> set[str]:
    """Collect all bare-identifier names referenced in an expression."""
    if isinstance(node, Ident):
        return {node.name} if node.name else set()
    names: set[str] = set()
    target = getattr(node, "target", None)
    if isinstance(target, Expr):
        names |= _names_from_ast(target)
    args = getattr(node, "args", None)
    if args:
        for arg in args:
            if isinstance(arg, Expr):
                names |= _names_from_ast(arg)
    operand = getattr(node, "operand", None)
    if isinstance(operand, Expr):
        names |= _names_from_ast(operand)
    elements = getattr(node, "elements", None)
    if elements:
        for elem in elements:
            if isinstance(elem, Expr):
                names |= _names_from_ast(elem)
    if isinstance(node, CreateList):
        for elem in node.elements:
            names |= _names_from_ast(elem)
    return names


def _cel_identifier_names(condition: CelExpr) -> set[str]:
    try:
        return _names_from_ast(parse_cel(str(condition)))
    except ParseError:
        return set()


def _synthetic_names_from_conditions(*condition_groups: tuple[CelExpr, ...] | list[CelExpr]) -> list[str]:
    names: set[str] = set()
    for group in condition_groups:
        for condition in group:
            for match in _cel_identifier_names(condition):
                if match not in _NON_BINDING_NAMES:
                    names.add(match)
    return sorted(names)


def _retry_with_standard_bindings(
    solver: Z3ConditionSolver,
    *,
    binding_conditions: tuple[CelExpr, ...] | list[CelExpr],
    claim_conditions: tuple[CelExpr, ...] | list[CelExpr],
    source_artifact: str | None,
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
        raise UnknownConceptInCEL(extra_names[0], source_artifact=source_artifact)
    if augmented_registry == dict(base_registry):
        return solver
    return Z3ConditionSolver(augmented_registry)


def is_claim_node_active(
    claim: ClaimNode,
    *,
    environment: Environment,
    solver: Z3ConditionSolver | None,
    lifting_system: LiftingSystem | None = None,
) -> bool:
    claim_context_id = _claim_context_id(claim)
    if not _claim_projected_into_environment(
        claim_context_id=claim_context_id,
        claim_id=str(claim.claim_id),
        environment=environment,
        lifting_system=lifting_system,
    ):
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
            source_artifact=_claim_node_source_artifact(claim),
        ).are_disjoint(
            binding_conditions,
            claim_conditions,
        )


def is_active_claim_active(
    claim: ActiveClaim,
    *,
    environment: Environment,
    solver: Z3ConditionSolver | None,
    lifting_system: LiftingSystem | None = None,
) -> bool:
    claim_context_id = claim.context_id
    if not _claim_projected_into_environment(
        claim_context_id=None if claim_context_id is None else str(claim_context_id),
        claim_id=str(claim.claim_id),
        environment=environment,
        lifting_system=lifting_system,
    ):
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
            source_artifact=claim.artifact_id,
        ).are_disjoint(
            binding_conditions,
            claim_conditions,
        )


def activate_compiled_world_graph(
    compiled: CompiledWorldGraph,
    *,
    environment: Environment,
    solver: Z3ConditionSolver,
    lifting_system: LiftingSystem | None = None,
) -> ActiveWorldGraph:
    active_claim_ids: list[ClaimId] = []
    inactive_claim_ids: list[ClaimId] = []

    for claim in compiled.claims:
        if is_claim_node_active(
            claim,
            environment=environment,
            solver=solver,
            lifting_system=lifting_system,
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

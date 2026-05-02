"""Graph-native activation over compiled semantic graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from propstore.core.active_claims import ActiveClaim
from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core.conditions import checked_condition_set
from propstore.core.conditions.cel_frontend import check_condition_ir
from propstore.core.conditions.registry import with_standard_synthetic_bindings
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions.solver import ConditionSolver, Z3TranslationError
from propstore.core.id_types import ClaimId
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph
from propstore.core.environment import Environment
from propstore.core.labels import binding_condition_to_cel

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


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


def _claim_node_source_artifact(claim: ClaimNode) -> str | None:
    if claim.provenance is not None and claim.provenance.source_id is not None:
        return claim.provenance.source_id
    return claim.claim_id


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


def _raise_unknown_concept_if_present(
    exc: ValueError,
    *,
    source_artifact: str | None,
) -> None:
    message = str(exc)
    prefix = "Undefined concept: '"
    if prefix not in message:
        return
    concept_name = message.split(prefix, 1)[1].split("'", 1)[0]
    raise UnknownConceptInCEL(concept_name, source_artifact=source_artifact) from exc


def _retry_with_standard_bindings(
    solver: ConditionSolver,
) -> ConditionSolver:
    base_registry = solver.registry
    augmented_registry = with_standard_synthetic_bindings(base_registry)
    if augmented_registry == dict(base_registry):
        return solver
    return ConditionSolver(augmented_registry)


def _binding_kind(value: object) -> KindType:
    if isinstance(value, bool):
        return KindType.BOOLEAN
    if isinstance(value, int | float):
        return KindType.QUANTITY
    return KindType.CATEGORY


def _solver_with_environment_bindings(
    solver: ConditionSolver,
    environment: Environment,
) -> ConditionSolver:
    registry = with_standard_synthetic_bindings(solver.registry)
    for name, value in environment.bindings.items():
        if name in registry:
            continue
        registry[name] = ConceptInfo(
            id=f"ps:binding:{name}",
            canonical_name=name,
            kind=_binding_kind(value),
            category_extensible=True,
        )
    if registry == dict(solver.registry):
        return solver
    return ConditionSolver(registry)


def is_claim_node_active(
    claim: ClaimNode,
    *,
    environment: Environment,
    solver: ConditionSolver | None,
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

    claim_conditions = claim.checked_conditions
    if claim_conditions is None or not claim_conditions.conditions:
        return True

    binding_conditions = _binding_conditions(environment)
    if not binding_conditions:
        return True
    if solver is None:
        raise ValueError("A condition solver is required for conditional activation")

    query_solver = _solver_with_environment_bindings(solver, environment)

    try:
        registry = query_solver.registry
        return not query_solver.are_disjoint(
            checked_condition_set(
                check_condition_ir(str(condition), registry)
                for condition in binding_conditions
            ),
            claim_conditions,
        )
    except ValueError as exc:
        _raise_unknown_concept_if_present(
            exc,
            source_artifact=_claim_node_source_artifact(claim),
        )
        raise
    except Z3TranslationError:
        retry_solver = _retry_with_standard_bindings(
            query_solver,
        )
        retry_registry = retry_solver.registry
        try:
            return not retry_solver.are_disjoint(
                checked_condition_set(
                    check_condition_ir(str(condition), retry_registry)
                    for condition in binding_conditions
                ),
                checked_condition_set(
                    check_condition_ir(source, retry_registry)
                    for source in claim_conditions.sources
                ),
            )
        except ValueError as exc:
            _raise_unknown_concept_if_present(
                exc,
                source_artifact=_claim_node_source_artifact(claim),
            )
            raise


def is_active_claim_active(
    claim: ActiveClaim,
    *,
    environment: Environment,
    solver: ConditionSolver | None,
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

    claim_conditions = claim.checked_conditions
    if claim_conditions is None or not claim_conditions.conditions:
        return True

    binding_conditions = _binding_conditions(environment)
    if not binding_conditions:
        return True
    if solver is None:
        raise ValueError("A condition solver is required for conditional activation")

    query_solver = _solver_with_environment_bindings(solver, environment)

    try:
        registry = query_solver.registry
        return not query_solver.are_disjoint(
            checked_condition_set(
                check_condition_ir(str(condition), registry)
                for condition in binding_conditions
            ),
            claim_conditions,
        )
    except ValueError as exc:
        _raise_unknown_concept_if_present(exc, source_artifact=claim.artifact_id)
        raise
    except Z3TranslationError:
        retry_solver = _retry_with_standard_bindings(
            query_solver,
        )
        retry_registry = retry_solver.registry
        try:
            return not retry_solver.are_disjoint(
                checked_condition_set(
                    check_condition_ir(str(condition), retry_registry)
                    for condition in binding_conditions
                ),
                checked_condition_set(
                    check_condition_ir(source, retry_registry)
                    for source in claim_conditions.sources
                ),
            )
        except ValueError as exc:
            _raise_unknown_concept_if_present(exc, source_artifact=claim.artifact_id)
            raise


def activate_compiled_world_graph(
    compiled: CompiledWorldGraph,
    *,
    environment: Environment,
    solver: ConditionSolver,
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

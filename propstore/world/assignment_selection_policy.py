"""Propstore adapter for the external assignment-selection package."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from assignment_selection import (
    Assignment,
    Constraint,
    MergeOperator,
    Problem,
    SourceAssignment,
    solve,
)

from propstore.cel_registry import build_store_cel_registry
from propstore.core.conditions import CheckedCondition
from propstore.core.conditions.cel_frontend import check_condition_ir
from propstore.core.conditions.registry import ConceptInfo, scope_condition_registry
from propstore.core.conditions.solver import ConditionSolver
from propstore.core.id_types import ClaimId
from propstore.families.claims.declaration import Claim
from propstore.families.concepts.declaration import Concept
from propstore.world.types import (
    IntegrityConstraint,
    IntegrityConstraintKind,
    RenderPolicy,
    WorldStore,
)


def _claim_id(claim: Claim) -> ClaimId:
    return ClaimId(str(claim.id))


def _claim_value(claim: Claim) -> float | str | None:
    numeric_payload = claim.numeric_payload
    value = None if numeric_payload is None else numeric_payload.value
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return value
    return None


def _claim_concept_id(claim: Claim) -> str:
    concept_id = None if claim.value_concept_id is None else str(claim.value_concept_id)
    if not isinstance(concept_id, str) or not concept_id:
        raise KeyError("resolution requires each claim to have a non-empty value concept")
    return concept_id


def _normalized_form_parameters(concept: Concept | None) -> Mapping[str, object]:
    if concept is None:
        return {}
    raw = concept.form_parameters
    if isinstance(raw, Mapping):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return parsed
    return {}


def _concept_integrity_constraints(
    world: WorldStore,
    concept_id: str,
) -> tuple[IntegrityConstraint, ...]:
    concept = world.get_concept(concept_id)
    if concept is None:
        return tuple()

    constraints: list[IntegrityConstraint] = []
    lower = concept.range_min
    upper = concept.range_max
    if lower is not None or upper is not None:
        constraints.append(
            IntegrityConstraint(
                kind=IntegrityConstraintKind.RANGE,
                concept_ids=(concept_id,),
                metadata={"lower": lower, "upper": upper},
                description="concept range",
            )
        )

    form_parameters = _normalized_form_parameters(concept)
    if concept.form == "category":
        values = form_parameters.get("values")
        extensible = form_parameters.get("extensible", True)
        if isinstance(values, list | tuple) and not extensible:
            constraints.append(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CATEGORY,
                    concept_ids=(concept_id,),
                    metadata={
                        "allowed_values": tuple(str(value) for value in values),
                        "extensible": False,
                    },
                    description="non-extensible category value set",
                )
            )

    return tuple(constraints)


def _filtered_assignment_selection_claim_rows(
    active_claim_rows: Sequence[Claim],
    policy: RenderPolicy | None,
) -> list[Claim]:
    branch_filter = None if policy is None else policy.branch_filter
    filtered: list[Claim] = []
    for claim in active_claim_rows:
        value = _claim_value(claim)
        if value is None:
            continue
        branch = claim.branch
        if (
            branch_filter is not None
            and isinstance(branch, str)
            and branch not in branch_filter
        ):
            continue
        filtered.append(claim)
    return filtered


def _integrity_constraint_concept_ids(constraints: Sequence[IntegrityConstraint]) -> set[str]:
    return {
        concept_id
        for constraint in constraints
        for concept_id in constraint.concept_ids
    }


def _cel_registry_for_concepts(
    world: WorldStore,
    concept_ids: Sequence[str],
) -> dict[str, ConceptInfo]:
    rows = [
        concept
        for concept_id in concept_ids
        if (concept := world.get_concept(concept_id)) is not None
    ]
    registry = build_store_cel_registry(rows)
    return scope_condition_registry(registry, tuple(concept_ids))


def _enriched_policy_integrity_constraints(
    world: WorldStore,
    constraints: Sequence[IntegrityConstraint],
) -> tuple[IntegrityConstraint, ...]:
    concept_ids = sorted(_integrity_constraint_concept_ids(constraints))
    cel_registry = _cel_registry_for_concepts(world, concept_ids)
    enriched: list[IntegrityConstraint] = []
    for constraint in constraints:
        metadata = dict(constraint.metadata)
        if constraint.kind == IntegrityConstraintKind.CEL and "registry" not in metadata:
            metadata["registry"] = cel_registry
        enriched.append(
            IntegrityConstraint(
                kind=constraint.kind,
                concept_ids=constraint.concept_ids,
                metadata=metadata,
                cel=constraint.cel,
                description=constraint.description,
            )
        )
    return tuple(enriched)


def _constraint_scope_values(
    assignment: Assignment,
    constraint: IntegrityConstraint,
) -> dict[str, Any]:
    return {
        concept_id: assignment.value_for(concept_id)
        for concept_id in constraint.concept_ids
    }


def _scoped_cel_registry(constraint: IntegrityConstraint) -> dict[str, ConceptInfo]:
    registry = constraint.metadata.get("registry")
    if not isinstance(registry, Mapping):
        raise TypeError("CEL integrity constraint requires metadata['registry']")
    return scope_condition_registry(registry, constraint.concept_ids)


def _cel_bindings(
    assignment: Assignment,
    constraint: IntegrityConstraint,
    registry: Mapping[str, ConceptInfo],
) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for canonical_name, info in registry.items():
        bindings[canonical_name] = assignment.value_for(info.id)
    return bindings


def _validate_cel_constraint(
    constraint: IntegrityConstraint,
) -> tuple[dict[str, ConceptInfo], CheckedCondition]:
    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = _scoped_cel_registry(constraint)
    try:
        checked = check_condition_ir(str(constraint.cel), registry)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return registry, checked


def _compile_integrity_constraint(constraint: IntegrityConstraint) -> Constraint:
    if constraint.kind == IntegrityConstraintKind.RANGE:
        lower = constraint.metadata.get("lower")
        upper = constraint.metadata.get("upper")

        def _holds(assignment: Assignment) -> bool:
            scoped_values = _constraint_scope_values(assignment, constraint)
            for value in scoped_values.values():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    return False
                if lower is not None and numeric < float(lower):
                    return False
                if upper is not None and numeric > float(upper):
                    return False
            return True

        return Constraint(
            concept_ids=constraint.concept_ids,
            holds=_holds,
            description=constraint.description,
        )

    if constraint.kind == IntegrityConstraintKind.CATEGORY:
        allowed_values = tuple(constraint.metadata.get("allowed_values", ()))
        extensible = bool(constraint.metadata.get("extensible", False))

        def _holds(assignment: Assignment) -> bool:
            if extensible:
                return True
            scoped_values = _constraint_scope_values(assignment, constraint)
            return all(value in allowed_values for value in scoped_values.values())

        return Constraint(
            concept_ids=constraint.concept_ids,
            holds=_holds,
            description=constraint.description,
        )

    if constraint.kind == IntegrityConstraintKind.CEL:
        registry, checked = _validate_cel_constraint(constraint)
        solver = ConditionSolver(registry)

        def _holds(assignment: Assignment) -> bool:
            bindings = _cel_bindings(assignment, constraint, registry)
            return solver.is_condition_satisfied(checked, bindings)

        return Constraint(
            concept_ids=constraint.concept_ids,
            holds=_holds,
            description=constraint.description,
        )

    if constraint.kind == IntegrityConstraintKind.CUSTOM:
        predicate = constraint.metadata.get("predicate")
        if not callable(predicate):
            raise TypeError("CUSTOM integrity constraint requires callable metadata['predicate']")

        def _holds(assignment: Assignment) -> bool:
            return bool(predicate(_constraint_scope_values(assignment, constraint)))

        return Constraint(
            concept_ids=constraint.concept_ids,
            holds=_holds,
            description=constraint.description,
        )

    raise ValueError(f"Unsupported integrity constraint kind: {constraint.kind}")


def build_assignment_selection_problem(
    active_claim_rows: Sequence[Claim],
    target_concept_id: str,
    *,
    world: WorldStore,
    policy: RenderPolicy | None,
) -> Problem:
    branch_weights = None if policy is None else policy.branch_weights
    merge_operator = (
        policy.merge_operator
        if policy is not None
        else MergeOperator.SIGMA
    )
    explicit_constraints = (
        tuple()
        if policy is None
        else _enriched_policy_integrity_constraints(world, policy.integrity_constraints)
    )
    concept_ids = {
        _claim_concept_id(claim)
        for claim in active_claim_rows
    }
    concept_ids.add(target_concept_id)
    concept_ids.update(_integrity_constraint_concept_ids(explicit_constraints))

    grouped: dict[str, dict[str, Claim]] = {}
    for claim in active_claim_rows:
        claim_id = _claim_id(claim)
        concept_id = _claim_concept_id(claim)
        branch = claim.branch
        source_id = branch if isinstance(branch, str) and branch else claim_id
        per_source = grouped.setdefault(str(source_id), {})
        if concept_id in per_source:
            raise ValueError(
                f"source '{source_id}' has multiple active claims for concept '{concept_id}'"
            )
        per_source[concept_id] = claim

    sources: list[SourceAssignment] = []
    for source_id, concept_claims in grouped.items():
        sample_claim = next(iter(concept_claims.values()))
        branch = sample_claim.branch
        weight = 1.0
        if branch_weights is not None and isinstance(branch, str) and branch:
            weight = float(branch_weights.get(branch, 1.0))
        sources.append(
            SourceAssignment(
                source_id=source_id,
                assignment=Assignment(
                    values={
                        concept_id: _claim_value(claim)
                        for concept_id, claim in concept_claims.items()
                    }
                ),
                weight=weight,
            )
        )

    automatic_constraints: list[IntegrityConstraint] = []
    for concept_id in sorted(concept_ids):
        automatic_constraints.extend(_concept_integrity_constraints(world, concept_id))

    return Problem(
        concept_ids=tuple(sorted(concept_ids)),
        sources=tuple(sources),
        constraints=tuple(
            _compile_integrity_constraint(constraint)
            for constraint in tuple(automatic_constraints) + explicit_constraints
        ),
        operator=MergeOperator(merge_operator),
    )


def resolve_assignment_selection_merge(
    target_claim_rows: Sequence[Claim],
    active_claim_rows: Sequence[Claim],
    concept_id: str,
    *,
    world: WorldStore,
    policy: RenderPolicy | None = None,
) -> tuple[str | None, str | None]:
    if world is None:
        return None, "assignment_selection_merge strategy requires an explicit artifact store"

    filtered_rows = _filtered_assignment_selection_claim_rows(active_claim_rows, policy)
    if not filtered_rows:
        return None, "no assignment-selection merge sources after branch filter"
    try:
        problem = build_assignment_selection_problem(
            filtered_rows,
            concept_id,
            world=world,
            policy=policy,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)

    result = solve(problem)
    if not result.winners:
        return None, result.reason

    target_values = {
        winner.value_for(concept_id)
        for winner in result.winners
    }
    if len(target_values) != 1:
        return None, f"{len(result.winners)} assignment-selection merge assignments disagree on target value"

    winning_value = next(iter(target_values))
    matching_claims = [
        claim
        for claim in target_claim_rows
        if _claim_value(claim) == winning_value
    ]
    if len(matching_claims) != 1:
        return None, (
            f"merged target value represented by {len(matching_claims)} active claims"
        )

    return str(_claim_id(matching_claims[0])), (
        f"global assignment-selection merge ({problem.operator}) winner satisfies {len(problem.constraints)} constraints across {len(problem.concept_ids)} concepts"
    )

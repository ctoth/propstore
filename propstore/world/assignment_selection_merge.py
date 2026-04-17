"""Assignment selection over observed typed assignments for propstore.

The primary production entrypoint is ``solve_assignment_selection_merge(problem)``, which solves
one assignment-level merge problem over a declared concept domain subject to an
integrity constraint ``mu``. Production resolution routes through that
global solver.

Konieczny 2002 defines merging over propositional belief bases with
min-over-models distance and an integrity constraint ``mu`` over models. This
module preserves the aggregation families (sum/max/leximax) but adapts them to
observed concept values rather than full belief-base model semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from collections.abc import Mapping
from typing import Any

from propstore.cel_checker import (
    check_cel_expr,
    scope_cel_registry,
)
from propstore.cel_types import CheckedCelExpr
from propstore.world.types import (
    AssignmentSelectionProblem,
    AssignmentSelectionResult,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeAssignmentScore,
    MergeOperator,
    MergeSource,
    normalize_merge_operator,
)


def claim_distance(a: Any, b: Any) -> float:
    """Distance between two claim values.

    Numeric values: absolute difference.
    Non-numeric: Hamming distance (0 if equal, 1 if different).

    Per Konieczny 2002 claim13/17: d(I, phi) is a distance metric
    between interpretations.
    """
    try:
        return abs(float(a) - float(b))
    except (ValueError, TypeError):
        return 0.0 if a == b else 1.0


def _unique_sources(sources: tuple[MergeSource, ...]) -> tuple[MergeSource, ...]:
    """Deduplicate equal assignments for arbitration-style operators."""
    result: list[MergeSource] = []
    for source in sources:
        if not any(
            existing.assignment.values == source.assignment.values
            and existing.weight == source.weight
            for existing in result
        ):
            result.append(source)
    return tuple(result)


def _assignment_tiebreak_key(
    assignment: MergeAssignment,
    concept_ids: tuple[str, ...],
) -> tuple[tuple[int, float | str], ...]:
    key: list[tuple[int, float | str]] = []
    for concept_id in concept_ids:
        value = assignment.value_for(concept_id)
        try:
            key.append((0, float(value)))
        except (TypeError, ValueError):
            key.append((1, repr(value)))
    return tuple(key)


def _score_sort_key(score: float | tuple[float, ...]) -> tuple[float, ...]:
    if isinstance(score, tuple):
        return score
    return (score,)


def enumerate_candidate_assignments(problem: AssignmentSelectionProblem) -> tuple[MergeAssignment, ...]:
    """Enumerate discrete candidate assignments from observed source values."""
    domains: list[list[Any]] = []
    for concept_id in problem.concept_ids:
        values: list[Any] = []
        for source in problem.sources:
            if concept_id in source.assignment.values and not any(
                existing == source.assignment.value_for(concept_id)
                for existing in values
            ):
                values.append(source.assignment.value_for(concept_id))
        if not values:
            return tuple()
        domains.append(values)

    result: list[MergeAssignment] = []
    for choice in product(*domains):
        assignment = MergeAssignment(
            values={
                concept_id: value
                for concept_id, value in zip(problem.concept_ids, choice, strict=True)
            }
        )
        if not any(existing.values == assignment.values for existing in result):
            result.append(assignment)
    return tuple(result)


def assignment_distance(assignment: MergeAssignment, source: MergeSource) -> float:
    """Distance between a candidate assignment and one source assignment."""
    distance = 0.0
    for concept_id, value in assignment.values.items():
        if concept_id not in source.assignment.values:
            continue
        distance += claim_distance(value, source.assignment.value_for(concept_id))
    return distance


def _constraint_scope_values(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
) -> dict[str, Any]:
    return {
        concept_id: assignment.value_for(concept_id)
        for concept_id in constraint.concept_ids
    }


def _scoped_cel_registry(constraint: IntegrityConstraint) -> dict[str, Any]:
    registry = constraint.metadata.get("registry")
    if not isinstance(registry, Mapping):
        raise TypeError("CEL integrity constraint requires metadata['registry']")
    return scope_cel_registry(registry, constraint.concept_ids)


def _cel_bindings(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for canonical_name, info in registry.items():
        bindings[canonical_name] = assignment.value_for(info.id)
    return bindings


def _validate_cel_constraint(constraint: IntegrityConstraint) -> tuple[dict[str, Any], CheckedCelExpr]:
    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = _scoped_cel_registry(constraint)
    try:
        checked = check_cel_expr(constraint.cel, registry)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return registry, checked


@dataclass(frozen=True)
class _CompiledConstraint:
    kind: IntegrityConstraintKind
    concept_ids: tuple[str, ...]
    holds: Any


def _eval_cel_constraint_z3(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
) -> bool:
    registry, checked = _validate_cel_constraint(constraint)
    bindings = _cel_bindings(assignment, constraint, registry)
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError as exc:
        raise RuntimeError("Z3 is required for CEL assignment-selection merge evaluation") from exc
    solver = Z3ConditionSolver(registry)
    return solver.is_condition_satisfied(checked, bindings)


def _compile_cel_constraint(
    constraint: IntegrityConstraint,
) -> _CompiledConstraint:
    registry, checked = _validate_cel_constraint(constraint)
    try:
        from propstore.z3_conditions import Z3ConditionSolver
    except ImportError as exc:
        raise RuntimeError("Z3 is required for CEL assignment-selection merge evaluation") from exc
    solver = Z3ConditionSolver(registry)

    def _holds(assignment: MergeAssignment) -> bool:
        bindings = _cel_bindings(assignment, constraint, registry)
        return solver.is_condition_satisfied(checked, bindings)

    return _CompiledConstraint(
        kind=constraint.kind,
        concept_ids=constraint.concept_ids,
        holds=_holds,
    )


def _compile_constraint(constraint: IntegrityConstraint) -> _CompiledConstraint:
    if constraint.kind == IntegrityConstraintKind.RANGE:
        lower = constraint.metadata.get("lower")
        upper = constraint.metadata.get("upper")

        def _holds(assignment: MergeAssignment) -> bool:
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

        return _CompiledConstraint(
            kind=constraint.kind,
            concept_ids=constraint.concept_ids,
            holds=_holds,
        )

    if constraint.kind == IntegrityConstraintKind.CATEGORY:
        allowed_values = tuple(constraint.metadata.get("allowed_values", ()))
        extensible = bool(constraint.metadata.get("extensible", False))

        def _holds(assignment: MergeAssignment) -> bool:
            if extensible:
                return True
            scoped_values = _constraint_scope_values(assignment, constraint)
            return all(value in allowed_values for value in scoped_values.values())

        return _CompiledConstraint(
            kind=constraint.kind,
            concept_ids=constraint.concept_ids,
            holds=_holds,
        )

    if constraint.kind == IntegrityConstraintKind.CEL:
        return _compile_cel_constraint(constraint)

    if constraint.kind == IntegrityConstraintKind.CUSTOM:
        predicate = constraint.metadata.get("predicate")
        if not callable(predicate):
            raise TypeError("CUSTOM integrity constraint requires callable metadata['predicate']")

        def _holds(assignment: MergeAssignment) -> bool:
            scoped_values = _constraint_scope_values(assignment, constraint)
            return bool(predicate(scoped_values))

        return _CompiledConstraint(
            kind=constraint.kind,
            concept_ids=constraint.concept_ids,
            holds=_holds,
        )

    raise ValueError(f"Unsupported integrity constraint kind: {constraint.kind}")


def _compile_constraints(
    constraints: tuple[IntegrityConstraint, ...] | list[IntegrityConstraint],
) -> tuple[_CompiledConstraint, ...]:
    return tuple(_compile_constraint(constraint) for constraint in constraints)


def _constraint_holds(
    assignment: MergeAssignment,
    constraint: _CompiledConstraint,
) -> bool:
    return bool(constraint.holds(assignment))


def assignment_satisfies_mu(problem: AssignmentSelectionProblem, assignment: MergeAssignment) -> bool:
    """Whether an assignment satisfies every integrity constraint in the problem."""
    compiled_constraints = _compile_constraints(problem.constraints)
    return all(_constraint_holds(assignment, constraint) for constraint in compiled_constraints)


def _score_assignment(
    problem: AssignmentSelectionProblem,
    assignment: MergeAssignment,
) -> float | tuple[float, ...]:
    operator = normalize_merge_operator(problem.operator)
    if operator == MergeOperator.SIGMA:
        return sum(
            source.weight * assignment_distance(assignment, source)
            for source in problem.sources
        )

    scored_sources = (
        _unique_sources(problem.sources)
        if operator in (MergeOperator.MAX, MergeOperator.GMAX)
        else problem.sources
    )
    distances = tuple(
        source.weight * assignment_distance(assignment, source)
        for source in scored_sources
    )
    if operator == MergeOperator.MAX:
        return max(distances, default=0.0)
    if operator == MergeOperator.GMAX:
        return tuple(sorted(distances, reverse=True))
    raise ValueError(f"Unknown merge operator: {problem.operator}")


def solve_assignment_selection_merge(problem: AssignmentSelectionProblem) -> AssignmentSelectionResult:
    """Solve one assignment-level assignment-selection merge problem over the declared concept domain."""
    candidates = enumerate_candidate_assignments(problem)
    compiled_constraints = _compile_constraints(problem.constraints)
    admissible = tuple(
        candidate
        for candidate in candidates
        if all(_constraint_holds(candidate, constraint) for constraint in compiled_constraints)
    )
    if not admissible:
        return AssignmentSelectionResult(
            winners=tuple(),
            scored_candidates=tuple(),
            admissible_count=0,
            total_candidate_count=len(candidates),
            reason="no admissible assignments",
        )

    scored = sorted(
        (
            MergeAssignmentScore(
                assignment=assignment,
                score=_score_assignment(problem, assignment),
            )
            for assignment in admissible
        ),
        key=lambda item: (
            _score_sort_key(item.score),
            _assignment_tiebreak_key(item.assignment, problem.concept_ids),
        ),
    )
    best_score = scored[0].score
    winners = tuple(item.assignment for item in scored if item.score == best_score)
    return AssignmentSelectionResult(
        winners=winners,
        scored_candidates=tuple(scored),
        admissible_count=len(admissible),
        total_candidate_count=len(candidates),
    )

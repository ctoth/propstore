"""Scalar adaptations of Konieczny 2002 aggregation operators.

Implements render-time aggregation kernels inspired by Konieczny & Pino Pérez
2002. Each operator takes a profile mapping source IDs to scalar claim values
and returns the winning value that minimizes aggregated distance.

- Sigma: minimizes sum of distances
- Max: minimizes maximum distance
- GMax: lexicographically compares sorted distance vectors

Konieczny 2002 defines merging over propositional belief bases with
min-over-models distance and an integrity constraint ``mu`` over models. This
module preserves the aggregation families (sum/max/leximax) but adapts them to
a scalar-value domain: numeric claims use absolute difference and categorical
claims use Hamming distance (0/1).

This module now provides:

- scalar aggregation kernels for legacy one-concept callers
- an assignment-level constrained solver for the adapted `mu` path

The implementation still does not provide full propositional IC merging in the
paper's sense. The current `mu` enforcement is an assignment-level adaptation
over observed concept values, not a model-theoretic operator over belief bases.
"""
from __future__ import annotations

from itertools import product
from collections.abc import Mapping
from typing import Any

from propstore.cel_checker import (
    ASTNode,
    BinaryOpNode,
    CelError,
    InNode,
    LiteralNode,
    NameNode,
    TernaryNode,
    UnaryOpNode,
    check_cel_expression,
    parse_cel,
)
from propstore.world.types import (
    ICMergeProblem,
    ICMergeResult,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeAssignmentScore,
    MergeOperator,
    MergeSource,
    normalize_merge_operator,
)


_SCALAR_CONCEPT_ID = "__value__"


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


def sigma_merge(profile: dict[str, Any]) -> Any:
    """Select the value minimizing sum distance to all profile values.

    Per Konieczny 2002 claim13-15: d_Sigma(I, Psi) = sum d(I, phi).

    Candidates are drawn from the profile values themselves (discrete selection,
    no interpolation). The majority value wins because it has the lowest total
    distance when counted with multiplicity.
    """
    candidates = list(profile.values())
    best_value = None
    best_score = float("inf")
    for candidate in candidates:
        score = sum(claim_distance(candidate, v) for v in candidates)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            # Stable tie-breaking: pick the smaller value for IC3 syntax independence.
            # Ensures result depends only on the multi-set of values, not key order.
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def _unique_values(profile: dict[str, Any]) -> list[Any]:
    """Deduplicate profile values, preserving order of first occurrence.

    Max and GMax satisfy the Arb property (Konieczny 2002 claim18-19):
    duplicating a source must not change the result. This requires computing
    distances against unique values only, so multiplicity is ignored.
    """
    result: list[Any] = []
    for v in profile.values():
        if not any(existing == v for existing in result):
            result.append(v)
    return result


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


def enumerate_candidate_assignments(problem: ICMergeProblem) -> tuple[MergeAssignment, ...]:
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


def _cel_errors_text(errors: list[CelError]) -> str:
    return "; ".join(error.message for error in errors)


def _scoped_cel_registry(constraint: IntegrityConstraint) -> dict[str, Any]:
    registry = constraint.metadata.get("registry")
    if not isinstance(registry, Mapping):
        raise TypeError("CEL integrity constraint requires metadata['registry']")
    scoped_ids = set(constraint.concept_ids)
    return {
        canonical_name: info
        for canonical_name, info in registry.items()
        if getattr(info, "id", None) in scoped_ids
    }


def _cel_bindings(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    bindings: dict[str, Any] = {}
    for canonical_name, info in registry.items():
        bindings[canonical_name] = assignment.value_for(info.id)
    return bindings


def _eval_cel_ast(node: ASTNode, bindings: Mapping[str, Any]) -> Any:
    if isinstance(node, LiteralNode):
        return node.value
    if isinstance(node, NameNode):
        if node.name not in bindings:
            raise ValueError(f"Undefined concept: '{node.name}'")
        return bindings[node.name]
    if isinstance(node, UnaryOpNode):
        operand = _eval_cel_ast(node.operand, bindings)
        if node.op == "!":
            return not operand
        if node.op == "-":
            return -operand
        raise ValueError(f"Unknown CEL unary operator: {node.op}")
    if isinstance(node, BinaryOpNode):
        left = _eval_cel_ast(node.left, bindings)
        right = _eval_cel_ast(node.right, bindings)
        if node.op == "&&":
            return bool(left) and bool(right)
        if node.op == "||":
            return bool(left) or bool(right)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "<":
            return left < right
        if node.op == ">":
            return left > right
        if node.op == "<=":
            return left <= right
        if node.op == ">=":
            return left >= right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        raise ValueError(f"Unknown CEL binary operator: {node.op}")
    if isinstance(node, InNode):
        expr = _eval_cel_ast(node.expr, bindings)
        return expr in [_eval_cel_ast(value, bindings) for value in node.values]
    if isinstance(node, TernaryNode):
        condition = _eval_cel_ast(node.condition, bindings)
        branch = node.true_branch if condition else node.false_branch
        return _eval_cel_ast(branch, bindings)
    raise TypeError(f"Unsupported CEL AST node: {type(node)}")


def _eval_cel_constraint(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
) -> bool:
    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = _scoped_cel_registry(constraint)
    errors = check_cel_expression(constraint.cel, registry)
    if errors:
        raise ValueError(_cel_errors_text(errors))
    bindings = _cel_bindings(assignment, constraint, registry)
    ast = parse_cel(constraint.cel)
    return bool(_eval_cel_ast(ast, bindings))


def _constraint_holds(
    assignment: MergeAssignment,
    constraint: IntegrityConstraint,
) -> bool:
    scoped_values = _constraint_scope_values(assignment, constraint)

    if constraint.kind == IntegrityConstraintKind.RANGE:
        lower = constraint.metadata.get("lower")
        upper = constraint.metadata.get("upper")
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

    if constraint.kind == IntegrityConstraintKind.CATEGORY:
        allowed_values = tuple(constraint.metadata.get("allowed_values", ()))
        extensible = bool(constraint.metadata.get("extensible", False))
        if extensible:
            return True
        for value in scoped_values.values():
            if value not in allowed_values:
                return False
        return True

    if constraint.kind == IntegrityConstraintKind.CEL:
        return _eval_cel_constraint(assignment, constraint)

    if constraint.kind == IntegrityConstraintKind.CUSTOM:
        predicate = constraint.metadata.get("predicate")
        return bool(predicate(scoped_values))

    raise ValueError(f"Unsupported integrity constraint kind: {constraint.kind}")


def assignment_satisfies_mu(problem: ICMergeProblem, assignment: MergeAssignment) -> bool:
    """Whether an assignment satisfies every integrity constraint in the problem."""
    return all(_constraint_holds(assignment, constraint) for constraint in problem.constraints)


def _score_assignment(
    problem: ICMergeProblem,
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


def solve_ic_merge(problem: ICMergeProblem) -> ICMergeResult:
    """Solve the constrained assignment-selection problem for one IC-merge instance."""
    candidates = enumerate_candidate_assignments(problem)
    admissible = tuple(
        candidate
        for candidate in candidates
        if assignment_satisfies_mu(problem, candidate)
    )
    if not admissible:
        return ICMergeResult(
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
    return ICMergeResult(
        winners=winners,
        scored_candidates=tuple(scored),
        admissible_count=len(admissible),
        total_candidate_count=len(candidates),
    )


def scalar_profile_problem(
    profile: Mapping[str, Any],
    *,
    operator: MergeOperator | str = MergeOperator.SIGMA,
    constraints: tuple[IntegrityConstraint, ...] = tuple(),
    concept_id: str = _SCALAR_CONCEPT_ID,
) -> ICMergeProblem:
    """Lift a scalar profile into the assignment-level IC-merge abstraction."""
    return ICMergeProblem(
        concept_ids=(concept_id,),
        sources=tuple(
            MergeSource(
                source_id=str(source_id),
                assignment=MergeAssignment(values={concept_id: value}),
            )
            for source_id, value in profile.items()
        ),
        constraints=constraints,
        operator=normalize_merge_operator(operator),
    )


def max_merge(profile: dict[str, Any]) -> Any:
    """Select the value minimizing maximum distance to the profile values.

    Per Konieczny 2002 claim17-18: d_Max(I, Psi) = max d(I, phi).

    Uses deduplicated values for both candidates and distance targets,
    ensuring the Arb property (insensitivity to source multiplicity).
    """
    unique = _unique_values(profile)
    best_value = None
    best_score = float("inf")
    for candidate in unique:
        score = max(claim_distance(candidate, v) for v in unique)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def gmax_merge(profile: dict[str, Any]) -> Any:
    """Lexicographically compare sorted distance vectors over profile values.

    Per Konieczny 2002 claim19-20: GMax refines Max.

    Uses deduplicated values for both candidates and distance targets,
    ensuring the Arb property (insensitivity to source multiplicity).
    For each candidate, compute its distance to every unique value, sort
    descending, then pick the candidate with the lexicographically smallest
    sorted vector.
    """
    unique = _unique_values(profile)
    best_value = None
    best_vector: list[float] | None = None
    for candidate in unique:
        distances = sorted(
            [claim_distance(candidate, v) for v in unique],
            reverse=True,
        )
        if best_vector is None or distances < best_vector:
            best_vector = distances
            best_value = candidate
        elif distances == best_vector and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def ic_merge(profile: dict[str, Any], *, operator: str = "sigma") -> Any:
    """Dispatch to the appropriate merge operator.

    Default is the Sigma aggregation kernel (Konieczny 2002 claim15).
    """
    # TODO: branch_weights from RenderPolicy not yet consumed.
    # When implemented, weighted_sigma would use w_i * d(I, phi_i)
    # per Konieczny 2002 weighted profile extension.
    dispatch = {
        "sigma": sigma_merge,
        "max": max_merge,
        "gmax": gmax_merge,
    }
    fn = dispatch.get(operator)
    if fn is None:
        raise ValueError(f"Unknown merge operator: {operator}")
    return fn(profile)

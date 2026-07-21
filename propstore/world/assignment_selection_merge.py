"""Assignment-selection merge over observed typed assignments for propstore.

The production entrypoint is ``solve_assignment_selection_merge(request)``, which
solves one assignment-level merge problem over a declared concept domain subject
to propstore integrity constraints. Production render-time resolution routes
through that global solver.

The merge math itself — candidate enumeration, distance-minimising consensus,
the sum/max/leximax (sigma/max/gmax) aggregation families, and integrity-
constraint filtering — is owned by the ``assignment_selection`` substrate
package (Konieczny 2002, adapted to observed concept values rather than full
belief-base model semantics). This module does not re-implement that solver. It
supplies the propstore-specific knowledge the generic package is parameterised
by: it compiles each propstore :class:`~propstore.world.types.IntegrityConstraint`
(``RANGE``/``CATEGORY``/``CEL``/``CUSTOM``) into the package's
:class:`~assignment_selection.Constraint` predicate — the CEL path evaluating
through ``condition_ir`` (CEL + Z3) — then builds the package's
:class:`~assignment_selection.Problem` and delegates to
:func:`assignment_selection.solve`.

The propstore request bundles package ``SourceAssignment`` sources and the
canonical ``MergeOperator`` with propstore ``IntegrityConstraint`` knowledge; it
is not a mirror of the package ``Problem`` (whose constraints are already-
compiled predicates).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from assignment_selection import (
    Assignment,
    Constraint,
    MergeOperator,
    Problem,
    Result,
    SourceAssignment,
    solve,
)
from condition_ir import (
    CheckedCondition,
    ConceptInfo,
    ConditionSolver,
    check_condition_ir,
    scope_condition_registry,
)

from propstore.world.types import IntegrityConstraint, IntegrityConstraintKind


@dataclass(frozen=True)
class AssignmentSelectionRequest:
    """A propstore assignment-selection merge request, lowered to the package on solve.

    Carries the package's :class:`~assignment_selection.SourceAssignment` sources
    and canonical :class:`~assignment_selection.MergeOperator` directly, plus the
    propstore :class:`~propstore.world.types.IntegrityConstraint` knowledge that
    :func:`solve_assignment_selection_merge` compiles into package
    :class:`~assignment_selection.Constraint` predicates before building the
    package :class:`~assignment_selection.Problem`. Concept-domain validation
    (unknown / duplicate concept ids) is performed by the package ``Problem`` at
    solve time.
    """

    concept_ids: tuple[str, ...]
    sources: tuple[SourceAssignment, ...]
    integrity_constraints: tuple[IntegrityConstraint, ...] = ()
    operator: MergeOperator = MergeOperator.SIGMA
    max_candidates: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(
            self, "integrity_constraints", tuple(self.integrity_constraints)
        )
        object.__setattr__(self, "operator", MergeOperator(self.operator))


def _scoped_cel_registry(constraint: IntegrityConstraint) -> dict[str, ConceptInfo]:
    # ``metadata`` is an untyped bag; the CEL contract is that ``metadata['registry']``
    # is a ``Mapping[str, ConceptInfo]``. Adopt that declared type on read so the
    # boundary is honest about what condition_ir requires.
    registry: Mapping[str, ConceptInfo] | None = constraint.metadata.get("registry")
    if not isinstance(registry, Mapping):
        raise TypeError("CEL integrity constraint requires metadata['registry']")
    return scope_condition_registry(registry, constraint.concept_ids)


def _validate_cel_constraint(
    constraint: IntegrityConstraint,
) -> tuple[dict[str, ConceptInfo], CheckedCondition]:
    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = _scoped_cel_registry(constraint)
    checked = check_condition_ir(str(constraint.cel), registry)
    return registry, checked


def _cel_bindings(
    assignment: Assignment,
    registry: Mapping[str, ConceptInfo],
) -> dict[str, object]:
    return {
        canonical_name: assignment.value_for(info.id)
        for canonical_name, info in registry.items()
    }


def _compile_cel_constraint(constraint: IntegrityConstraint) -> Constraint:
    registry, checked = _validate_cel_constraint(constraint)
    solver = ConditionSolver(registry)

    def _holds(assignment: Assignment) -> bool:
        return solver.is_condition_satisfied(
            checked, _cel_bindings(assignment, registry)
        )

    return Constraint(
        concept_ids=constraint.concept_ids,
        holds=_holds,
        description=constraint.description,
    )


def _compile_range_constraint(constraint: IntegrityConstraint) -> Constraint:
    lower_meta = constraint.metadata.get("lower")
    upper_meta = constraint.metadata.get("upper")
    lower = None if lower_meta is None else float(lower_meta)
    upper = None if upper_meta is None else float(upper_meta)
    concept_ids = constraint.concept_ids

    def _holds(assignment: Assignment) -> bool:
        for concept_id in concept_ids:
            value = assignment.value_for(concept_id)
            if not isinstance(value, (int, float, str)):
                return False
            try:
                numeric = float(value)
            except ValueError:
                return False
            if lower is not None and numeric < lower:
                return False
            if upper is not None and numeric > upper:
                return False
        return True

    return Constraint(
        concept_ids=concept_ids,
        holds=_holds,
        description=constraint.description,
    )


def _compile_category_constraint(constraint: IntegrityConstraint) -> Constraint:
    allowed_values: tuple[object, ...] | list[object] | None = constraint.metadata.get(
        "allowed_values"
    )
    allowed: tuple[object, ...] = (
        () if allowed_values is None else tuple(allowed_values)
    )
    extensible = bool(constraint.metadata.get("extensible", False))
    concept_ids = constraint.concept_ids

    def _holds(assignment: Assignment) -> bool:
        if extensible:
            return True
        return all(
            assignment.value_for(concept_id) in allowed for concept_id in concept_ids
        )

    return Constraint(
        concept_ids=concept_ids,
        holds=_holds,
        description=constraint.description,
    )


def _compile_custom_constraint(constraint: IntegrityConstraint) -> Constraint:
    predicate = constraint.metadata.get("predicate")
    if not callable(predicate):
        raise TypeError(
            "CUSTOM integrity constraint requires callable metadata['predicate']"
        )
    typed_predicate: Callable[[Mapping[str, object]], object] = predicate
    concept_ids = constraint.concept_ids

    def _holds(assignment: Assignment) -> bool:
        scoped = {
            concept_id: assignment.value_for(concept_id) for concept_id in concept_ids
        }
        return bool(typed_predicate(scoped))

    return Constraint(
        concept_ids=concept_ids,
        holds=_holds,
        description=constraint.description,
    )


_CONSTRAINT_COMPILERS: dict[
    IntegrityConstraintKind, Callable[[IntegrityConstraint], Constraint]
] = {
    IntegrityConstraintKind.RANGE: _compile_range_constraint,
    IntegrityConstraintKind.CATEGORY: _compile_category_constraint,
    IntegrityConstraintKind.CEL: _compile_cel_constraint,
    IntegrityConstraintKind.CUSTOM: _compile_custom_constraint,
}


def _compile_constraint(constraint: IntegrityConstraint) -> Constraint:
    compiler = _CONSTRAINT_COMPILERS.get(constraint.kind)
    if compiler is None:
        raise ValueError(f"Unsupported integrity constraint kind: {constraint.kind}")
    return compiler(constraint)


def _compile_constraints(
    constraints: tuple[IntegrityConstraint, ...],
) -> tuple[Constraint, ...]:
    return tuple(_compile_constraint(constraint) for constraint in constraints)


def assignment_satisfies_mu(
    request: AssignmentSelectionRequest,
    assignment: Assignment,
) -> bool:
    """Whether ``assignment`` satisfies every integrity constraint in ``request``.

    Each compiled predicate reads only its own declared concept ids, so the full
    assignment may be passed directly (matching the package's per-constraint
    scoping at solve time).
    """
    compiled = _compile_constraints(request.integrity_constraints)
    return all(constraint.holds(assignment) for constraint in compiled)


def solve_assignment_selection_merge(request: AssignmentSelectionRequest) -> Result:
    """Solve one assignment-level assignment-selection merge over the declared domain.

    Compiles the request's propstore integrity constraints into package
    predicates, builds the package :class:`~assignment_selection.Problem`, and
    delegates the merge to :func:`assignment_selection.solve`. The returned
    :class:`~assignment_selection.Result` is the package's canonical result type.
    """
    problem = Problem(
        concept_ids=request.concept_ids,
        sources=request.sources,
        constraints=_compile_constraints(request.integrity_constraints),
        operator=request.operator,
    )
    return solve(problem, max_candidates=request.max_candidates)

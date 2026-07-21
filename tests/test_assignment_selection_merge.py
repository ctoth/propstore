"""Tests for propstore's assignment-selection merge glue.

The merge math (sigma/max/gmax aggregation, distance-minimising consensus,
candidate enumeration, integrity filtering) lives in the ``assignment_selection``
substrate package and is tested there. These tests cover the *propstore* surface:
compiling propstore :class:`IntegrityConstraint` values (RANGE/CATEGORY/CEL/CUSTOM)
into package predicates, the CEL path through ``condition_ir`` (CEL + Z3), and the
delegation in :func:`solve_assignment_selection_merge`. Test-local scalar Konieczny
oracles are kept only to cross-check that the delegation produces the expected
distance-minimising winner.
"""

from __future__ import annotations

from itertools import product
from typing import Any

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import propstore.storage as repo_api
import propstore.world.assignment_selection_merge as merge_module
from assignment_selection import Assignment, MergeOperator, SourceAssignment
from assignment_selection.solver import claim_distance, enumerate_candidate_assignments
from condition_ir import ConceptInfo, KindType
from propstore.world.assignment_selection_merge import (
    AssignmentSelectionRequest,
    _compile_cel_constraint,
    assignment_satisfies_mu,
    solve_assignment_selection_merge,
)
from propstore.world.types import (
    IntegrityConstraint,
    IntegrityConstraintKind,
    RenderPolicy,
    ResolutionStrategy,
)


# ── Builders ─────────────────────────────────────────────────────────


def _numeric_cel_registry(*concept_ids: str) -> dict[str, ConceptInfo]:
    return {
        concept_id: ConceptInfo(
            id=concept_id,
            canonical_name=concept_id,
            kind=KindType.QUANTITY,
        )
        for concept_id in concept_ids
    }


def _source(source_id: str, values: dict[str, Any]) -> SourceAssignment:
    return SourceAssignment(source_id=source_id, assignment=Assignment(values))


def _scalar_request(
    profile: dict[str, Any],
    *,
    operator: MergeOperator = MergeOperator.SIGMA,
    constraints: tuple[IntegrityConstraint, ...] = (),
    concept_id: str = "__value__",
) -> AssignmentSelectionRequest:
    return AssignmentSelectionRequest(
        concept_ids=(concept_id,),
        sources=tuple(
            _source(str(source_id), {concept_id: value})
            for source_id, value in profile.items()
        ),
        integrity_constraints=constraints,
        operator=operator,
    )


# ── Scalar Konieczny oracles (cross-check only) ──────────────────────


def _unique_values(profile: dict[str, Any]) -> list[Any]:
    result: list[Any] = []
    for value in profile.values():
        if not any(existing == value for existing in result):
            result.append(value)
    return result


def _select_min(candidates: list[Any], score: Any) -> Any:
    best_value = None
    best_score: Any = None
    for candidate in candidates:
        candidate_score = score(candidate)
        if best_score is None or candidate_score < best_score:
            best_score = candidate_score
            best_value = candidate
        elif candidate_score == best_score and best_value is not None:
            if float(candidate) < float(best_value):
                best_value = candidate
    return best_value


def _sigma_merge(profile: dict[str, Any]) -> Any:
    candidates = list(profile.values())
    return _select_min(
        candidates,
        lambda c: sum(claim_distance(c, value) for value in candidates),
    )


def _max_merge(profile: dict[str, Any]) -> Any:
    unique = _unique_values(profile)
    return _select_min(
        unique,
        lambda c: max(claim_distance(c, value) for value in unique),
    )


def _gmax_merge(profile: dict[str, Any]) -> Any:
    unique = _unique_values(profile)
    return _select_min(
        unique,
        lambda c: sorted((claim_distance(c, value) for value in unique), reverse=True),
    )


def _scalar_merge(profile: dict[str, Any], *, operator: MergeOperator) -> Any:
    if operator is MergeOperator.SIGMA:
        return _sigma_merge(profile)
    if operator is MergeOperator.MAX:
        return _max_merge(profile)
    return _gmax_merge(profile)


# ── CEL bruteforce oracle (differential check on the compiled predicate) ──


def _eval_cel_ast_oracle(node: Any, bindings: dict[str, Any]) -> Any:
    from cel_parser import (
        OP_ADD,
        OP_AND,
        OP_DIV,
        OP_EQ,
        OP_GE,
        OP_GT,
        OP_IN,
        OP_LE,
        OP_LT,
        OP_MUL,
        OP_NE,
        OP_NEG,
        OP_NOT,
        OP_OR,
        OP_SUB,
        OP_TERNARY,
        BoolLit,
        Call,
        CreateList,
        DoubleLit,
        Ident,
        IntLit,
        StringLit,
        UintLit,
    )

    if isinstance(node, (IntLit, UintLit, DoubleLit, StringLit, BoolLit)):
        return node.value
    if isinstance(node, Ident):
        if node.name not in bindings:
            raise ValueError(f"Undefined concept: '{node.name}'")
        return bindings[node.name]
    if isinstance(node, Call) and node.target is None:
        fn = node.function
        if fn == OP_NOT and len(node.args) == 1:
            return not _eval_cel_ast_oracle(node.args[0], bindings)
        if fn == OP_NEG and len(node.args) == 1:
            return -_eval_cel_ast_oracle(node.args[0], bindings)
        if fn == OP_TERNARY and len(node.args) == 3:
            cond = _eval_cel_ast_oracle(node.args[0], bindings)
            branch = node.args[1] if cond else node.args[2]
            return _eval_cel_ast_oracle(branch, bindings)
        if fn == OP_IN and len(node.args) == 2:
            element = _eval_cel_ast_oracle(node.args[0], bindings)
            list_expr = node.args[1]
            if not isinstance(list_expr, CreateList):
                raise TypeError("'in' rhs must be a list literal")
            return element in [
                _eval_cel_ast_oracle(value, bindings) for value in list_expr.elements
            ]
        if len(node.args) == 2:
            left = _eval_cel_ast_oracle(node.args[0], bindings)
            right = _eval_cel_ast_oracle(node.args[1], bindings)
            if fn == OP_AND:
                return bool(left) and bool(right)
            if fn == OP_OR:
                return bool(left) or bool(right)
            if fn == OP_ADD:
                return left + right
            if fn == OP_SUB:
                return left - right
            if fn == OP_MUL:
                return left * right
            if fn == OP_DIV:
                return left / right
            if fn == OP_LT:
                return left < right
            if fn == OP_GT:
                return left > right
            if fn == OP_LE:
                return left <= right
            if fn == OP_GE:
                return left >= right
            if fn == OP_EQ:
                return left == right
            if fn == OP_NE:
                return left != right
        raise ValueError(f"Unknown CEL operator: {fn}")
    raise TypeError(f"Unsupported CEL AST node: {type(node).__name__}")


def _eval_cel_constraint_bruteforce(
    assignment: Assignment, constraint: IntegrityConstraint
) -> bool:
    from cel_parser import parse as parse_cel
    from condition_ir import check_cel_expression, scope_condition_registry

    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = scope_condition_registry(
        constraint.metadata["registry"],
        constraint.concept_ids,
    )
    errors = check_cel_expression(str(constraint.cel), registry)
    hard_errors = [error for error in errors if not error.is_warning]
    if hard_errors:
        raise ValueError("; ".join(error.message for error in hard_errors))
    bindings = {
        canonical_name: assignment.value_for(info.id)
        for canonical_name, info in registry.items()
    }
    ast = parse_cel(str(constraint.cel))
    return bool(_eval_cel_ast_oracle(ast, bindings))


# ── Strategies ───────────────────────────────────────────────────────

st_claim_value = st.floats(
    min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False
)
st_branch_profile = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st_claim_value,
    min_size=2,
    max_size=5,
)
st_small_pairs = st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)
    ),
    min_size=2,
    max_size=5,
)
st_operator = st.sampled_from(list(MergeOperator))


# ── Delegation correctness ───────────────────────────────────────────


class TestDelegation:
    def test_two_concept_problem_returns_assignment_winner(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(
                _source("s1", {"x": 0.0, "y": 0.0}),
                _source("s2", {"x": 0.0, "y": 1.0}),
                _source("s3", {"x": 1.0, "y": 1.0}),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners == (Assignment({"x": 0.0, "y": 1.0}),)
        assert result.scored_candidates[0].assignment == Assignment(
            {"x": 0.0, "y": 1.0}
        )

    @pytest.mark.property
    @given(st_branch_profile, st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_unconstrained_single_concept_matches_scalar_oracle(
        self,
        profile: dict[str, float],
        operator: MergeOperator,
    ) -> None:
        result = solve_assignment_selection_merge(
            _scalar_request(profile, operator=operator)
        )

        assert result.scored_candidates
        assert result.scored_candidates[0].assignment.value_for(
            "__value__"
        ) == _scalar_merge(
            profile,
            operator=operator,
        )

    @pytest.mark.property
    @given(st_small_pairs, st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_source_order_does_not_change_winners(
        self,
        source_pairs: list[tuple[int, int]],
        operator: MergeOperator,
    ) -> None:
        forward = solve_assignment_selection_merge(
            AssignmentSelectionRequest(
                concept_ids=("x", "y"),
                sources=tuple(
                    _source(f"s{index}", {"x": x, "y": y})
                    for index, (x, y) in enumerate(source_pairs)
                ),
                operator=operator,
            )
        )
        reverse = solve_assignment_selection_merge(
            AssignmentSelectionRequest(
                concept_ids=("x", "y"),
                sources=tuple(
                    _source(f"r{index}", {"x": x, "y": y})
                    for index, (x, y) in enumerate(reversed(source_pairs))
                ),
                operator=operator,
            )
        )

        assert forward.winners == reverse.winners

    @pytest.mark.property
    @given(st_branch_profile, st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_source_renaming_does_not_change_best_assignment(
        self,
        profile: dict[str, float],
        operator: MergeOperator,
    ) -> None:
        renamed = {
            f"renamed_{index}": value for index, value in enumerate(profile.values())
        }

        original = solve_assignment_selection_merge(
            _scalar_request(profile, operator=operator)
        )
        result = solve_assignment_selection_merge(
            _scalar_request(renamed, operator=operator)
        )

        assert original.scored_candidates and result.scored_candidates
        assert original.scored_candidates[0].assignment.value_for(
            "__value__"
        ) == result.scored_candidates[0].assignment.value_for("__value__")


# ── CEL constraint compilation (condition_ir / Z3) ───────────────────


class TestCelConstraints:
    def test_cel_constraint_filters_assignments_by_canonical_name(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(
                _source("s1", {"x": 0.0, "y": 0.0}),
                _source("s2", {"x": 0.0, "y": 1.0}),
                _source("s3", {"x": 1.0, "y": 1.0}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel="x + y <= 1",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners == (Assignment({"x": 0.0, "y": 1.0}),)
        assert all(
            assignment_satisfies_mu(request, winner) for winner in result.winners
        )

    def test_invalid_cel_constraint_fails_explicitly(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(
                _source("s1", {"x": 0.0, "y": 0.0}),
                _source("s2", {"x": 1.0, "y": 1.0}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel="missing > 0",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        with pytest.raises(ValueError, match="Undefined concept"):
            solve_assignment_selection_merge(request)

    def test_open_category_constraint_allows_undeclared_literal(self) -> None:
        registry = {
            "task": ConceptInfo(
                id="task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "singing"],
                category_extensible=True,
            )
        }
        request = AssignmentSelectionRequest(
            concept_ids=("task",),
            sources=(
                _source("s1", {"task": "speech"}),
                _source("s2", {"task": "yodel"}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("task",),
                    cel="task == 'yodel'",
                    metadata={"registry": registry},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners == (Assignment({"task": "yodel"}),)

    def test_open_category_inequality_does_not_collapse_to_closed_domain(self) -> None:
        registry = {
            "task": ConceptInfo(
                id="task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "singing"],
                category_extensible=True,
            )
        }
        request = AssignmentSelectionRequest(
            concept_ids=("task",),
            sources=(
                _source("s1", {"task": "speech"}),
                _source("s2", {"task": "singing"}),
                _source("s3", {"task": "yodel"}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("task",),
                    cel="task != 'speech'",
                    metadata={"registry": registry},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(request)

        assert result.admissible_count == 2
        assert all(
            winner.value_for("task") in {"singing", "yodel"}
            for winner in result.winners
        )

    def test_cel_constraints_reuse_one_solver_per_problem(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        real_solver = merge_module.ConditionSolver
        init_count = 0

        class CountingSolver(real_solver):
            def __init__(self, registry: Any, **kwargs: Any) -> None:
                nonlocal init_count
                init_count += 1
                super().__init__(registry, **kwargs)

        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(
                _source("s1", {"x": 0.0, "y": 0.0}),
                _source("s2", {"x": 0.0, "y": 1.0}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel="x + y <= 1",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        monkeypatch.setattr(merge_module, "ConditionSolver", CountingSolver)
        result = solve_assignment_selection_merge(request)

        assert result.winners
        assert init_count == 1

    @pytest.mark.property
    @given(st_small_pairs, st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_always_true_cel_constraint_preserves_winners(
        self,
        source_pairs: list[tuple[int, int]],
        operator: MergeOperator,
    ) -> None:
        sources = tuple(
            _source(f"s{index}", {"x": x, "y": y})
            for index, (x, y) in enumerate(source_pairs)
        )
        unconstrained = solve_assignment_selection_merge(
            AssignmentSelectionRequest(
                concept_ids=("x", "y"), sources=sources, operator=operator
            )
        )
        constrained = solve_assignment_selection_merge(
            AssignmentSelectionRequest(
                concept_ids=("x", "y"),
                sources=sources,
                integrity_constraints=(
                    IntegrityConstraint(
                        kind=IntegrityConstraintKind.CEL,
                        concept_ids=("x", "y"),
                        cel="x == x && y == y",
                        metadata={"registry": _numeric_cel_registry("x", "y")},
                    ),
                ),
                operator=operator,
            )
        )

        assert constrained.winners == unconstrained.winners

    @pytest.mark.property
    @given(st_small_pairs, st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_unsatisfiable_cel_constraint_yields_no_winners(
        self,
        source_pairs: list[tuple[int, int]],
        operator: MergeOperator,
    ) -> None:
        result = solve_assignment_selection_merge(
            AssignmentSelectionRequest(
                concept_ids=("x", "y"),
                sources=tuple(
                    _source(f"s{index}", {"x": x, "y": y})
                    for index, (x, y) in enumerate(source_pairs)
                ),
                integrity_constraints=(
                    IntegrityConstraint(
                        kind=IntegrityConstraintKind.CEL,
                        concept_ids=("x", "y"),
                        cel="x < x",
                        metadata={"registry": _numeric_cel_registry("x", "y")},
                    ),
                ),
                operator=operator,
            )
        )

        assert result.winners == ()
        assert result.reason == "no admissible assignments"

    @pytest.mark.property
    @pytest.mark.differential
    @given(st_small_pairs, st.integers(min_value=0, max_value=4))
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_compiled_cel_predicate_agrees_with_bruteforce(
        self,
        source_pairs: list[tuple[int, int]],
        limit: int,
    ) -> None:
        constraint = IntegrityConstraint(
            kind=IntegrityConstraintKind.CEL,
            concept_ids=("x", "y"),
            cel=f"x + y <= {limit}",
            metadata={"registry": _numeric_cel_registry("x", "y")},
        )
        problem_sources = tuple(
            _source(f"s{index}", {"x": x, "y": y})
            for index, (x, y) in enumerate(source_pairs)
        )
        from assignment_selection import Problem

        candidates = enumerate_candidate_assignments(
            Problem(concept_ids=("x", "y"), sources=problem_sources)
        )
        compiled = _compile_cel_constraint(constraint)
        for assignment in candidates:
            assert compiled.holds(assignment) == _eval_cel_constraint_bruteforce(
                assignment, constraint
            )


# ── RANGE / CATEGORY / CUSTOM constraint compilation ─────────────────


class TestStructuredConstraints:
    def test_range_constraint_filters_admissible_winners(self) -> None:
        request = _scalar_request(
            {"b1": 5.0, "b2": 10.0, "b3": 50.0},
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": 0.0, "upper": 20.0},
                ),
            ),
        )

        result = solve_assignment_selection_merge(request)

        assert [winner.value_for("__value__") for winner in result.winners] == [10.0]
        assert result.admissible_count == 2

    def test_category_constraint_rejects_non_member_values(self) -> None:
        request = _scalar_request(
            {"b1": "speech", "b2": "whisper", "b3": "song"},
            operator=MergeOperator.MAX,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CATEGORY,
                    concept_ids=("__value__",),
                    metadata={
                        "allowed_values": ("speech", "whisper"),
                        "extensible": False,
                    },
                ),
            ),
        )

        result = solve_assignment_selection_merge(request)

        assert result.admissible_count == 2
        assert all(
            winner.value_for("__value__") in {"speech", "whisper"}
            for winner in result.winners
        )

    def test_cross_concept_custom_constraint_changes_winner_set(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(
                _source("s1", {"x": 0.0, "y": 0.0}),
                _source("s2", {"x": 0.0, "y": 1.0}),
                _source("s3", {"x": 1.0, "y": 0.0}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={
                        "predicate": lambda values: values["x"] + values["y"] == 1.0
                    },
                    description="x and y must sum to exactly 1",
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        independent = Assignment({"x": 0.0, "y": 0.0})
        assert not assignment_satisfies_mu(request, independent)

        result = solve_assignment_selection_merge(request)

        assert result.winners == (
            Assignment({"x": 0.0, "y": 1.0}),
            Assignment({"x": 1.0, "y": 0.0}),
        )

    def test_custom_constraint_is_scoped_to_declared_concepts(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y", "z"),
            sources=(
                _source("s1", {"x": 0, "y": 0, "z": 0}),
                _source("s2", {"x": 1, "y": 1, "z": 1}),
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={"predicate": lambda values: set(values) == {"x", "y"}},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners
        assert result.admissible_count == 8

    @pytest.mark.property
    @given(st_small_pairs, st.integers(min_value=0, max_value=4), st_operator)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_cross_concept_winners_always_satisfy_custom_mu(
        self,
        source_pairs: list[tuple[int, int]],
        max_sum: int,
        operator: MergeOperator,
    ) -> None:
        x_values = {x for x, _ in source_pairs}
        y_values = {y for _, y in source_pairs}
        assume(any(x + y <= max_sum for x, y in product(x_values, y_values)))

        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=tuple(
                _source(f"s{index}", {"x": x, "y": y})
                for index, (x, y) in enumerate(source_pairs)
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={
                        "predicate": lambda values, limit=max_sum: (
                            values["x"] + values["y"] <= limit
                        )
                    },
                    description="sum-bounded cross-concept admissibility",
                ),
            ),
            operator=operator,
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners
        assert all(
            assignment_satisfies_mu(request, winner) for winner in result.winners
        )

    @pytest.mark.property
    @given(st_branch_profile)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_winners_always_satisfy_range_mu(self, profile: dict[str, float]) -> None:
        ordered = sorted(profile.values())
        upper = ordered[len(ordered) // 2]
        request = _scalar_request(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": ordered[0], "upper": upper},
                ),
            ),
        )

        result = solve_assignment_selection_merge(request)

        assert result.winners
        assert all(
            assignment_satisfies_mu(request, winner) for winner in result.winners
        )

    @pytest.mark.property
    @given(
        st.sets(st.integers(min_value=0, max_value=2), min_size=1, max_size=3),
        st.sets(st.integers(min_value=0, max_value=2), min_size=1, max_size=3),
        st_operator,
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_separable_range_constraints_factorize_across_concepts(
        self,
        x_domain: set[int],
        y_domain: set[int],
        operator: MergeOperator,
    ) -> None:
        source_pairs = list(product(sorted(x_domain), sorted(y_domain)))
        x_values = sorted(x_domain)
        y_values = sorted(y_domain)
        x_upper = x_values[min(len(x_values) - 1, len(x_values) // 2)]
        y_upper = y_values[min(len(y_values) - 1, len(y_values) // 2)]

        global_request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=tuple(
                _source(f"s{index}", {"x": x, "y": y})
                for index, (x, y) in enumerate(source_pairs)
            ),
            integrity_constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("x",),
                    metadata={"lower": x_values[0], "upper": x_upper},
                ),
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("y",),
                    metadata={"lower": y_values[0], "upper": y_upper},
                ),
            ),
            operator=operator,
        )

        x_result = solve_assignment_selection_merge(
            _scalar_request(
                {f"x{i}": v for i, v in enumerate(x_values)},
                operator=operator,
                concept_id="x",
                constraints=(
                    IntegrityConstraint(
                        kind=IntegrityConstraintKind.RANGE,
                        concept_ids=("x",),
                        metadata={"lower": x_values[0], "upper": x_upper},
                    ),
                ),
            )
        )
        y_result = solve_assignment_selection_merge(
            _scalar_request(
                {f"y{i}": v for i, v in enumerate(y_values)},
                operator=operator,
                concept_id="y",
                constraints=(
                    IntegrityConstraint(
                        kind=IntegrityConstraintKind.RANGE,
                        concept_ids=("y",),
                        metadata={"lower": y_values[0], "upper": y_upper},
                    ),
                ),
            )
        )

        global_result = solve_assignment_selection_merge(global_request)
        expected = tuple(
            Assignment(
                {"x": x_assignment.value_for("x"), "y": y_assignment.value_for("y")}
            )
            for x_assignment, y_assignment in product(
                x_result.winners, y_result.winners
            )
        )

        assert global_result.winners == expected


# ── Concept-domain validation (delegated to the package Problem) ──────


class TestProblemValidation:
    def test_rejects_source_assignment_outside_declared_concepts(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "y"),
            sources=(_source("s1", {"x": 0.0, "z": 1.0}),),
            operator=MergeOperator.SIGMA,
        )
        with pytest.raises(ValueError, match="unknown concept ids"):
            solve_assignment_selection_merge(request)

    def test_rejects_duplicate_concept_ids(self) -> None:
        request = AssignmentSelectionRequest(
            concept_ids=("x", "x"),
            sources=(_source("s1", {"x": 0.0}),),
            operator=MergeOperator.SIGMA,
        )
        with pytest.raises(ValueError, match="duplicate concept ids"):
            solve_assignment_selection_merge(request)


# ── RenderPolicy integration ─────────────────────────────────────────


class TestRenderPolicyIntegration:
    def test_render_policy_has_merge_operator_default_sigma(self) -> None:
        assert RenderPolicy().merge_operator == MergeOperator.SIGMA

    def test_render_policy_has_branch_filter(self) -> None:
        assert RenderPolicy().branch_filter is None

    def test_resolution_strategy_has_assignment_selection_merge(self) -> None:
        assert (
            ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE
            == "assignment_selection_merge"
        )

    def test_render_policy_round_trips_merge_operator_enum(self) -> None:
        restored = RenderPolicy(merge_operator=MergeOperator.GMAX)
        assert restored.merge_operator == MergeOperator.GMAX


# ── Public-API honesty ───────────────────────────────────────────────


class TestPublicApiHonesty:
    def test_storage_does_not_export_merge_entrypoints(self) -> None:
        storage_all = getattr(repo_api, "__all__", ())
        assert not hasattr(repo_api, "solve_assignment_selection_merge")
        for name in (
            "solve_assignment_selection_merge",
            "AssignmentSelectionRequest",
            "MergeOperator",
            "assignment_selection_merge",
        ):
            assert name not in storage_all

    def test_module_docs_point_to_global_solver(self) -> None:
        module_doc = merge_module.__doc__ or ""
        assert "solve_assignment_selection_merge" in module_doc
        assert "assignment-level" in module_doc.lower()
        assert "scalar helper" not in module_doc.lower()
        assert not hasattr(merge_module, "_scalar_assignment_selection_merge")
        assert not hasattr(merge_module, "_scalar_profile_problem")
        assert not hasattr(merge_module, "_eval_cel_ast")
        assert not hasattr(merge_module, "_eval_cel_constraint_bruteforce")

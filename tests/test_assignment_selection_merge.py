"""Propstore-owned assignment-selection adapter, CEL, policy, and API tests."""

from __future__ import annotations

import importlib

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection import Assignment, MergeOperator, Problem, SourceAssignment
from assignment_selection import solve as package_solve
from assignment_selection.solver import (
    assignment_satisfies,
    enumerate_candidate_assignments,
)

from propstore.core.conditions.registry import ConditionRegistry, ConceptInfo, KindType
import propstore.storage as repo_api
from propstore.world import assignment_selection_policy as assignment_selection_adapter
from propstore.world.assignment_selection_policy import _compile_integrity_constraint
from propstore.world.types import (
    IntegrityConstraint,
    IntegrityConstraintKind,
    RenderPolicy,
    ResolutionStrategy,
)


def _numeric_cel_registry(*concept_ids: str) -> ConditionRegistry:
    return ConditionRegistry(
        {
            concept_id: ConceptInfo(
                id=concept_id,
                canonical_name=concept_id,
                kind=KindType.QUANTITY,
            )
            for concept_id in concept_ids
        }
    )


def _compile_problem(problem: Problem) -> Problem:
    return Problem(
        concept_ids=problem.concept_ids,
        sources=problem.sources,
        constraints=tuple(
            _compile_integrity_constraint(constraint)
            for constraint in problem.constraints
        ),
        operator=problem.operator,
    )


def _solve(problem: Problem):
    return package_solve(_compile_problem(problem))


def _satisfies(problem: Problem, assignment: Assignment) -> bool:
    return assignment_satisfies(_compile_problem(problem), assignment)


def _eval_cel_ast_oracle(node, bindings):
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


def _eval_cel_constraint_bruteforce_oracle(assignment, constraint) -> bool:
    from cel_parser import parse as parse_cel
    from propstore.core.conditions.cel_frontend import check_cel_expression

    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = constraint.metadata["registry"].scope(constraint.concept_ids)
    errors = check_cel_expression(constraint.cel, registry)
    hard_errors = [error for error in errors if not error.is_warning]
    if hard_errors:
        raise ValueError("; ".join(error.message for error in hard_errors))
    bindings = {
        canonical_name: assignment.value_for(info.id)
        for canonical_name, info in registry.items()
    }
    ast = parse_cel(constraint.cel)
    return bool(_eval_cel_ast_oracle(ast, bindings))


class TestAssignmentSelectionCelAdapter:
    def test_cel_constraint_filters_assignments_by_canonical_name(self):
        problem = Problem(
            concept_ids=("x", "y"),
            sources=(
                SourceAssignment("s1", Assignment(values={"x": 0.0, "y": 0.0})),
                SourceAssignment("s2", Assignment(values={"x": 0.0, "y": 1.0})),
                SourceAssignment("s3", Assignment(values={"x": 1.0, "y": 1.0})),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel="x + y <= 1",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = _solve(problem)

        assert result.winners == (Assignment(values={"x": 0.0, "y": 1.0}),)
        assert all(_satisfies(problem, winner) for winner in result.winners)

    def test_invalid_cel_constraint_fails_explicitly(self):
        problem = Problem(
            concept_ids=("x", "y"),
            sources=(
                SourceAssignment("s1", Assignment(values={"x": 0.0, "y": 0.0})),
                SourceAssignment("s2", Assignment(values={"x": 1.0, "y": 1.0})),
            ),
            constraints=(
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
            _solve(problem)

    def test_open_category_constraint_allows_undeclared_literal(self):
        extensible_category_registry = {
            "task": ConceptInfo(
                id="task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "singing"],
                category_extensible=True,
            )
        }
        problem = Problem(
            concept_ids=("task",),
            sources=(
                SourceAssignment("s1", Assignment(values={"task": "speech"})),
                SourceAssignment("s2", Assignment(values={"task": "yodel"})),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("task",),
                    cel="task == 'yodel'",
                    metadata={"registry": extensible_category_registry},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = _solve(problem)

        assert result.winners == (Assignment(values={"task": "yodel"}),)

    def test_duplicate_production_cel_runtime_is_removed(self):
        assert not hasattr(assignment_selection_adapter, "_eval_cel_ast")
        assert not hasattr(
            assignment_selection_adapter, "_eval_cel_constraint_bruteforce"
        )

    def test_cel_constraints_reuse_one_solver_per_problem(self, monkeypatch):
        real_solver = assignment_selection_adapter.ConditionSolver
        init_count = 0

        class CountingSolver(real_solver):
            def __init__(self, registry):
                nonlocal init_count
                init_count += 1
                super().__init__(registry)

        problem = Problem(
            concept_ids=("x", "y"),
            sources=(
                SourceAssignment("s1", Assignment(values={"x": 0.0, "y": 0.0})),
                SourceAssignment("s2", Assignment(values={"x": 0.0, "y": 1.0})),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel="x + y <= 1",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        monkeypatch.setattr(
            assignment_selection_adapter, "ConditionSolver", CountingSolver
        )
        result = _solve(problem)

        assert result.winners
        assert init_count == 1

    @pytest.mark.property
    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=2),
                st.integers(min_value=0, max_value=2),
            ),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_unsatisfiable_cel_constraint_yields_no_winners(
        self, source_pairs, operator
    ):
        result = _solve(
            Problem(
                concept_ids=("x", "y"),
                sources=tuple(
                    SourceAssignment(
                        source_id=f"s{index}",
                        assignment=Assignment(values={"x": x, "y": y}),
                    )
                    for index, (x, y) in enumerate(source_pairs)
                ),
                constraints=(
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

        assert result.winners == tuple()
        assert result.reason == "no admissible assignments"

    @pytest.mark.property
    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=2),
                st.integers(min_value=0, max_value=2),
            ),
            min_size=2,
            max_size=5,
        ),
        st.integers(min_value=0, max_value=4),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_solver_and_bruteforce_cel_agree_on_bounded_cases(
        self, source_pairs, limit
    ):
        problem = Problem(
            concept_ids=("x", "y"),
            sources=tuple(
                SourceAssignment(
                    source_id=f"s{index}",
                    assignment=Assignment(values={"x": x, "y": y}),
                )
                for index, (x, y) in enumerate(source_pairs)
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("x", "y"),
                    cel=f"x + y <= {limit}",
                    metadata={"registry": _numeric_cel_registry("x", "y")},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )
        constraint = problem.constraints[0]
        compiled = _compile_integrity_constraint(constraint)

        for assignment in enumerate_candidate_assignments(problem):
            assert compiled.holds(assignment) == _eval_cel_constraint_bruteforce_oracle(
                assignment,
                constraint,
            )


class TestRenderPolicyIntegration:
    def test_render_policy_has_merge_operator(self):
        policy = RenderPolicy()
        assert policy.merge_operator == "sigma"

    def test_render_policy_has_branch_filter(self):
        policy = RenderPolicy()
        assert policy.branch_filter is None

    def test_resolution_strategy_has_assignment_selection_merge(self):
        assert (
            ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE
            == "assignment_selection_merge"
        )

    def test_render_policy_round_trips_merge_operator_enum(self):
        policy = RenderPolicy(merge_operator=MergeOperator.GMAX)

        restored = RenderPolicy.from_dict(policy.to_dict())

        assert restored.merge_operator == "gmax"


class TestPublicApiHonesty:
    def test_repo_public_api_does_not_export_assignment_selection_package(self):
        assert not hasattr(repo_api, "assignment_selection")
        assert "assignment_selection" not in repo_api.__all__
        assert "MergeOperator" not in repo_api.__all__

    def test_old_assignment_selection_module_path_is_deleted(self):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("propstore.world." + "assignment_selection_merge")

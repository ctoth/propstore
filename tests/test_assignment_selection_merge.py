"""Propstore-owned assignment-selection adapter, CEL, policy, and API tests.

Pure assignment-selection algorithm tests live in the extracted
``assignment-selection`` package.
"""

from __future__ import annotations

import importlib

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from propstore.core.conditions.registry import ConceptInfo, KindType
import propstore.storage as repo_api
from propstore.world.assignment_selection_merge import (
    MergeOperator,
    _eval_cel_constraint_z3,
    assignment_satisfies_mu,
    enumerate_candidate_assignments,
    solve_assignment_selection_merge,
)
from propstore.world.types import (
    AssignmentSelectionProblem,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeSource,
    RenderPolicy,
    ResolutionStrategy,
)


assignment_selection_module = importlib.import_module("propstore.world.assignment_selection_merge")


def _numeric_cel_registry(*concept_ids: str) -> dict[str, ConceptInfo]:
    return {
        concept_id: ConceptInfo(
            id=concept_id,
            canonical_name=concept_id,
            kind=KindType.QUANTITY,
        )
        for concept_id in concept_ids
    }


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
    from propstore.core.conditions.registry import scope_condition_registry

    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = scope_condition_registry(
        constraint.metadata["registry"],
        constraint.concept_ids,
    )
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
        problem = AssignmentSelectionProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource("s1", MergeAssignment(values={"x": 0.0, "y": 0.0})),
                MergeSource("s2", MergeAssignment(values={"x": 0.0, "y": 1.0})),
                MergeSource("s3", MergeAssignment(values={"x": 1.0, "y": 1.0})),
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

        result = solve_assignment_selection_merge(problem)

        assert result.winners == (MergeAssignment(values={"x": 0.0, "y": 1.0}),)
        assert all(assignment_satisfies_mu(problem, winner) for winner in result.winners)

    def test_invalid_cel_constraint_fails_explicitly(self):
        problem = AssignmentSelectionProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource("s1", MergeAssignment(values={"x": 0.0, "y": 0.0})),
                MergeSource("s2", MergeAssignment(values={"x": 1.0, "y": 1.0})),
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
            solve_assignment_selection_merge(problem)

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
        problem = AssignmentSelectionProblem(
            concept_ids=("task",),
            sources=(
                MergeSource("s1", MergeAssignment(values={"task": "speech"})),
                MergeSource("s2", MergeAssignment(values={"task": "yodel"})),
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

        result = solve_assignment_selection_merge(problem)

        assert result.winners == (MergeAssignment(values={"task": "yodel"}),)

    def test_open_category_inequality_does_not_collapse_to_closed_domain(self):
        extensible_category_registry = {
            "task": ConceptInfo(
                id="task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "singing"],
                category_extensible=True,
            )
        }
        problem = AssignmentSelectionProblem(
            concept_ids=("task",),
            sources=(
                MergeSource("s1", MergeAssignment(values={"task": "speech"})),
                MergeSource("s2", MergeAssignment(values={"task": "singing"})),
                MergeSource("s3", MergeAssignment(values={"task": "yodel"})),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CEL,
                    concept_ids=("task",),
                    cel="task != 'speech'",
                    metadata={"registry": extensible_category_registry},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_assignment_selection_merge(problem)

        assert result.admissible_count == 2
        assert all(
            winner.value_for("task") in {"singing", "yodel"}
            for winner in result.winners
        )

    def test_duplicate_production_cel_runtime_is_removed(self):
        assert not hasattr(assignment_selection_module, "_eval_cel_ast")
        assert not hasattr(assignment_selection_module, "_eval_cel_constraint_bruteforce")

    def test_cel_constraints_reuse_one_solver_per_problem(self, monkeypatch):
        real_solver = assignment_selection_module.ConditionSolver
        init_count = 0

        class CountingSolver(real_solver):
            def __init__(self, registry):
                nonlocal init_count
                init_count += 1
                super().__init__(registry)

        problem = AssignmentSelectionProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource("s1", MergeAssignment(values={"x": 0.0, "y": 0.0})),
                MergeSource("s2", MergeAssignment(values={"x": 0.0, "y": 1.0})),
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

        monkeypatch.setattr(assignment_selection_module, "ConditionSolver", CountingSolver)
        result = solve_assignment_selection_merge(problem)

        assert result.winners
        assert init_count == 1

    @pytest.mark.property
    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_always_true_cel_constraint_preserves_winners(self, source_pairs, operator):
        sources = tuple(
            MergeSource(
                source_id=f"s{index}",
                assignment=MergeAssignment(values={"x": x, "y": y}),
            )
            for index, (x, y) in enumerate(source_pairs)
        )
        unconstrained = solve_assignment_selection_merge(
            AssignmentSelectionProblem(
                concept_ids=("x", "y"),
                sources=sources,
                operator=operator,
            )
        )
        constrained = solve_assignment_selection_merge(
            AssignmentSelectionProblem(
                concept_ids=("x", "y"),
                sources=sources,
                constraints=(
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
    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_unsatisfiable_cel_constraint_yields_no_winners(self, source_pairs, operator):
        result = solve_assignment_selection_merge(
            AssignmentSelectionProblem(
                concept_ids=("x", "y"),
                sources=tuple(
                    MergeSource(
                        source_id=f"s{index}",
                        assignment=MergeAssignment(values={"x": x, "y": y}),
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
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.integers(min_value=0, max_value=4),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_z3_and_bruteforce_cel_agree_on_bounded_cases(self, source_pairs, limit):
        problem = AssignmentSelectionProblem(
            concept_ids=("x", "y"),
            sources=tuple(
                MergeSource(
                    source_id=f"s{index}",
                    assignment=MergeAssignment(values={"x": x, "y": y}),
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

        for assignment in enumerate_candidate_assignments(problem):
            assert _eval_cel_constraint_z3(assignment, constraint) == _eval_cel_constraint_bruteforce_oracle(
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
        assert ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE == "assignment_selection_merge"

    def test_render_policy_round_trips_merge_operator_enum(self):
        policy = RenderPolicy(merge_operator=MergeOperator.GMAX)

        restored = RenderPolicy.from_dict(policy.to_dict())

        assert restored.merge_operator == MergeOperator.GMAX


class TestPublicApiHonesty:
    def test_repo_public_api_does_not_export_world_assignment_selection_entrypoints(self):
        assert not hasattr(repo_api, "solve_assignment_selection_merge")
        assert "solve_assignment_selection_merge" not in repo_api.__all__
        assert "claim_distance" not in repo_api.__all__
        assert "MergeOperator" not in repo_api.__all__
        assert "AssignmentSelectionProblem" not in repo_api.__all__
        assert "AssignmentSelectionResult" not in repo_api.__all__
        assert "scalar_profile_problem" not in repo_api.__all__
        assert "sigma_merge" not in repo_api.__all__
        assert "max_merge" not in repo_api.__all__
        assert "gmax_merge" not in repo_api.__all__
        assert "assignment_selection_merge" not in repo_api.__all__

    def test_assignment_selection_module_docs_point_to_global_solver(self):
        module_doc = assignment_selection_module.__doc__ or ""

        assert "solve_assignment_selection_merge" in module_doc
        assert "assignment-level" in module_doc.lower()
        assert "scalar helper" not in module_doc.lower()
        assert not hasattr(assignment_selection_module, "_scalar_assignment_selection_merge")
        assert not hasattr(assignment_selection_module, "_scalar_profile_problem")
        assert not hasattr(assignment_selection_module, "_eval_cel_ast")
        assert not hasattr(assignment_selection_module, "_eval_cel_constraint_bruteforce")

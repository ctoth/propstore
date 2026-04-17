"""Tests for global IC-merge and test-local one-concept oracle kernels.

These tests treat assignment-level ``solve_ic_merge`` as the main production
surface. The one-concept scalar kernels live in this test module only as
oracles for degenerate reductions and operator properties.
"""
from __future__ import annotations

import importlib
from itertools import product

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from propstore.cel_checker import ConceptInfo, KindType
import propstore.storage as repo_api
from propstore.world.ic_merge import (
    MergeOperator,
    _eval_cel_constraint_z3,
    assignment_satisfies_mu,
    enumerate_candidate_assignments,
    claim_distance,
    solve_ic_merge,
)
from propstore.world.types import (
    ICMergeProblem,
    IntegrityConstraint,
    IntegrityConstraintKind,
    MergeAssignment,
    MergeSource,
    RenderPolicy,
    ResolutionStrategy,
)

ic_merge_module = importlib.import_module("propstore.world.ic_merge")


def _eval_cel_ast_oracle(node, bindings):
    from propstore.cel_checker import (
        BinaryOpNode,
        InNode,
        LiteralNode,
        NameNode,
        TernaryNode,
        UnaryOpNode,
    )

    if isinstance(node, LiteralNode):
        return node.value
    if isinstance(node, NameNode):
        if node.name not in bindings:
            raise ValueError(f"Undefined concept: '{node.name}'")
        return bindings[node.name]
    if isinstance(node, UnaryOpNode):
        operand = _eval_cel_ast_oracle(node.operand, bindings)
        if node.op == "!":
            return not operand
        if node.op == "-":
            return -operand
        raise ValueError(f"Unknown CEL unary operator: {node.op}")
    if isinstance(node, BinaryOpNode):
        left = _eval_cel_ast_oracle(node.left, bindings)
        right = _eval_cel_ast_oracle(node.right, bindings)
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
        expr = _eval_cel_ast_oracle(node.expr, bindings)
        return expr in [_eval_cel_ast_oracle(value, bindings) for value in node.values]
    if isinstance(node, TernaryNode):
        condition = _eval_cel_ast_oracle(node.condition, bindings)
        branch = node.true_branch if condition else node.false_branch
        return _eval_cel_ast_oracle(branch, bindings)
    raise TypeError(f"Unsupported CEL AST node: {type(node)}")


def _eval_cel_constraint_bruteforce_oracle(assignment, constraint) -> bool:
    from propstore.cel_checker import check_cel_expression, parse_cel, scope_cel_registry

    if not constraint.cel:
        raise ValueError("CEL integrity constraint requires a non-empty cel expression")
    registry = scope_cel_registry(constraint.metadata["registry"], constraint.concept_ids)
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

# ── Strategies ──────────────────────────────────────────────────────

# Strategy: numeric claim values in the current scalar adaptation
st_claim_value = st.floats(
    min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False
)

# Strategy: a branch profile (2-5 branches, each with a numeric value)
st_branch_profile = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st_claim_value,
    min_size=2,
    max_size=5,
)

# Strategy: merge operator selection
st_operator = st.sampled_from(["sigma", "max", "gmax"])

# Strategy: branch weights (positive floats)
st_branch_weights = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    min_size=2,
    max_size=5,
)

st_small_assignment_value = st.integers(min_value=0, max_value=2)


def _numeric_cel_registry(*concept_ids: str) -> dict[str, ConceptInfo]:
    return {
        concept_id: ConceptInfo(
            id=concept_id,
            canonical_name=concept_id,
            kind=KindType.QUANTITY,
        )
        for concept_id in concept_ids
    }


def _unique_values(profile: dict[str, object]) -> list[object]:
    result: list[object] = []
    for value in profile.values():
        if not any(existing == value for existing in result):
            result.append(value)
    return result


def _sigma_merge(profile: dict[str, object]) -> object:
    candidates = list(profile.values())
    best_value = None
    best_score = float("inf")
    for candidate in candidates:
        score = sum(claim_distance(candidate, value) for value in candidates)
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


def _max_merge(profile: dict[str, object]) -> object:
    unique = _unique_values(profile)
    best_value = None
    best_score = float("inf")
    for candidate in unique:
        score = max(claim_distance(candidate, value) for value in unique)
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


def _gmax_merge(profile: dict[str, object]) -> object:
    unique = _unique_values(profile)
    best_value = None
    best_vector: list[float] | None = None
    for candidate in unique:
        distances = sorted(
            [claim_distance(candidate, value) for value in unique],
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


def _scalar_ic_merge(profile: dict[str, object], *, operator: str = "sigma") -> object:
    dispatch = {
        "sigma": _sigma_merge,
        "max": _max_merge,
        "gmax": _gmax_merge,
    }
    fn = dispatch.get(operator)
    if fn is None:
        raise ValueError(f"Unknown merge operator: {operator}")
    return fn(profile)


def _scalar_profile_problem(
    profile: dict[str, object],
    *,
    operator: MergeOperator | str = MergeOperator.SIGMA,
    constraints: tuple[IntegrityConstraint, ...] = tuple(),
    concept_id: str = "__value__",
) -> ICMergeProblem:
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
        operator=operator,
    )

# ── Group 1: MergeOperator Enum and Distance Function ──────────────


class TestMergeOperatorEnum:
    def test_merge_operator_enum(self):
        """MergeOperator has sigma, max, gmax values."""
        assert MergeOperator.SIGMA == "sigma"
        assert MergeOperator.MAX == "max"
        assert MergeOperator.GMAX == "gmax"


class TestClaimDistance:
    def test_claim_distance_numeric(self):
        """Distance between numeric claims is absolute difference.

        Per Konieczny 2002 claim13/17: d(I, phi) is a distance metric
        between interpretations.
        """
        assert claim_distance(3.0, 5.0) == 2.0
        assert claim_distance(5.0, 3.0) == 2.0  # symmetric

    def test_claim_distance_identical(self):
        """Distance between identical values is 0.

        Per Konieczny 2002: metric identity axiom d(x,x) = 0.
        """
        assert claim_distance(7.0, 7.0) == 0.0

    def test_claim_distance_categorical(self):
        """Distance between categorical (non-numeric) claims is Hamming:
        0 if equal, 1 if different.

        Per Konieczny 2002: distance generalises to non-numeric domains
        via Hamming distance.
        """
        assert claim_distance("alpha", "alpha") == 0.0
        assert claim_distance("alpha", "beta") == 1.0

    @given(st_claim_value, st_claim_value)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_distance_symmetric(self, a, b):
        """Distance is symmetric: d(a,b) == d(b,a).

        Per Konieczny 2002: distance is a metric, symmetry is a
        required axiom.
        """
        assert claim_distance(a, b) == claim_distance(b, a)

    @given(st_claim_value)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_distance_zero_self(self, a):
        """Distance from self is zero: d(a,a) == 0.

        Per Konieczny 2002: metric identity axiom.
        """
        assert claim_distance(a, a) == 0.0


# ── Group 2: Sigma Operator (scalar sum-distance adaptation) ───────


class TestSigmaMerge:
    def test_sigma_unanimous(self):
        """When all branches agree, sigma returns the common value.

        In the scalar adaptation, unanimous profiles are fixed points.
        """
        profile = {"b1": 5.0, "b2": 5.0, "b3": 5.0}
        result = _sigma_merge(profile)
        assert result == 5.0

    def test_sigma_majority_wins(self):
        """Majority value wins under sigma.

        Per Konieczny 2002 claim15: Sigma satisfies Maj — enough copies
        of a source dominate the result.
        """
        profile = {"b1": 10.0, "b2": 10.0, "b3": 10.0, "b4": 99.0}
        result = _sigma_merge(profile)
        assert result == 10.0  # 3 vs 1, majority wins

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        The scalar result depends on the multiset of values, not source labels.
        """
        result1 = _sigma_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = _sigma_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_result_in_value_set(self, profile):
        """Sigma result is one of the input values (for discrete profiles).

        The winning interpretation must be a value that actually appears
        in the profile — sigma selects, it does not interpolate.
        """
        result = _sigma_merge(profile)
        assert result in profile.values()

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_sigma_result_closure(self, profile):
        """Sigma result is always one of the input values (closure over candidate set).

        This verifies discrete selection: the merge operator picks from the
        profile values, it does not interpolate.
        """
        assume(len(set(profile.values())) >= 2)  # at least two distinct values
        result = _sigma_merge(profile)
        assert result in profile.values()


# ── Group 3: Max Operator (scalar max-distance adaptation) ─────────


class TestMaxMerge:
    def test_max_unanimous(self):
        """When all agree, max returns common value.

        In the scalar adaptation, unanimous profiles are fixed points.
        """
        profile = {"b1": 5.0, "b2": 5.0}
        result = _max_merge(profile)
        assert result == 5.0

    def test_max_minimizes_worst_case(self):
        """Max picks the value minimizing the maximum distance to any branch.

        Per Konieczny 2002 claim17: d_Max(I, Psi) = max d(I, phi).
        The result minimizes the worst-case distance across all sources.

        Candidates: 0 -> max_dist=100, 10 -> max_dist=90, 100 -> max_dist=100.
        Winner: 10.0.
        """
        profile = {"b1": 0.0, "b2": 10.0, "b3": 100.0}
        result = _max_merge(profile)
        assert result == 10.0

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_max_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        The scalar result depends on values, not source labels.
        """
        result1 = _max_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = _max_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_max_arbitration(self, profile):
        """Duplicating a source does not change the result.

        Per Konieczny 2002 claim18: Max satisfies Arb — the result is
        insensitive to source multiplicity.
        """
        result1 = _max_merge(profile)
        first_key = next(iter(profile))
        augmented = {**profile, f"{first_key}_dup": profile[first_key]}
        result2 = _max_merge(augmented)
        assert result1 == result2

    def test_max_duplicate_invariance_exposes_scalar_limit(self):
        """Max ignores source multiplicity in the scalar adaptation.

        This is the arbitration-style property the current implementation really
        enforces. It should not be confused with the paper's full fairness
        postulates, which require a model-theoretic result space.
        """
        profile_majority = {"b1": 0.0, "b2": 0.0, "b3": 0.0, "b4": 10.0}
        result = _max_merge(profile_majority)
        single_profile = {"b1": 0.0, "b2": 10.0}
        single_result = _max_merge(single_profile)
        assert result == single_result

    def test_max_handles_unhashable_values(self):
        """Max must deduplicate equal unhashable values without crashing."""
        profile = {"b1": [1], "b2": [1], "b3": [2]}
        result = _max_merge(profile)
        assert result == [1]


# ── Group 4: GMax Operator (scalar leximax adaptation) ─────────────


class TestGMaxMerge:
    def test_gmax_unanimous(self):
        """When all agree, gmax returns common value.

        In the scalar adaptation, unanimous profiles are fixed points.
        """
        profile = {"b1": 5.0, "b2": 5.0}
        result = _gmax_merge(profile)
        assert result == 5.0

    def test_gmax_refines_max(self):
        """GMax result is always in the Max result set.

        Per Konieczny 2002 claim20: Delta^GMax entails Delta^Max.
        GMax refines Max by breaking ties lexicographically on sorted
        distance vectors.
        """
        profile = {"b1": 0.0, "b2": 10.0, "b3": 5.0}
        gmax_result = _gmax_merge(profile)
        max_result = _max_merge(profile)
        # GMax must pick a value whose max distance is no worse than Max's pick
        gmax_max_dist = max(abs(gmax_result - v) for v in profile.values())
        max_max_dist = max(abs(max_result - v) for v in profile.values())
        assert gmax_max_dist <= max_max_dist + 1e-9  # float tolerance

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_refines_max_property(self, profile):
        """Property: GMax always refines Max.

        Per Konieczny 2002 claim20: for any profile Psi,
        Delta^GMax(Psi) entails Delta^Max(Psi).
        """
        gmax_result = _gmax_merge(profile)
        max_result = _max_merge(profile)
        gmax_max_dist = max(abs(gmax_result - v) for v in profile.values())
        max_max_dist = max(abs(max_result - v) for v in profile.values())
        assert gmax_max_dist <= max_max_dist + 1e-9

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_ic3_syntax_independence(self, profile):
        """Reordering branches produces same result.

        The scalar result depends on values, not source labels.
        """
        result1 = _gmax_merge(profile)
        reversed_profile = dict(reversed(list(profile.items())))
        result2 = _gmax_merge(reversed_profile)
        assert result1 == result2

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_gmax_arbitration(self, profile):
        """Duplicating a source does not change the result.

        Per Konieczny 2002 claim19: GMax satisfies Arb — the result is
        insensitive to source multiplicity.
        """
        result1 = _gmax_merge(profile)
        first_key = next(iter(profile))
        augmented = {**profile, f"{first_key}_dup": profile[first_key]}
        result2 = _gmax_merge(augmented)
        assert result1 == result2

    def test_gmax_handles_unhashable_values(self):
        """GMax must deduplicate equal unhashable values without crashing."""
        profile = {
            "b1": {"value": 1},
            "b2": {"value": 1},
            "b3": {"value": 2},
        }
        result = _gmax_merge(profile)
        assert result == {"value": 1}


# ── Group 5: Scalar Kernel Dispatcher ───────────────────────────────


class TestIcMergeDispatcher:
    def test_ic_merge_dispatches_sigma(self):
        """_scalar_ic_merge with operator='sigma' delegates to _sigma_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert _scalar_ic_merge(profile, operator="sigma") == _sigma_merge(profile)

    def test_ic_merge_dispatches_max(self):
        """_scalar_ic_merge with operator='max' delegates to _max_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert _scalar_ic_merge(profile, operator="max") == _max_merge(profile)

    def test_ic_merge_dispatches_gmax(self):
        """_scalar_ic_merge with operator='gmax' delegates to _gmax_merge."""
        profile = {"b1": 5.0, "b2": 5.0}
        assert _scalar_ic_merge(profile, operator="gmax") == _gmax_merge(profile)

    def test_ic_merge_default_is_sigma(self):
        """Default operator is sigma (majority).

        Sigma is the default aggregation kernel in the current scalar adapter.
        """
        profile = {"b1": 5.0, "b2": 10.0, "b3": 5.0}
        assert _scalar_ic_merge(profile) == _sigma_merge(profile)


class TestAssignmentLevelICMerge:
    def test_cel_constraint_filters_assignments_by_canonical_name(self):
        problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 1.0}),
                ),
                MergeSource(
                    source_id="s3",
                    assignment=MergeAssignment(values={"x": 1.0, "y": 1.0}),
                ),
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

        result = solve_ic_merge(problem)

        assert result.winners == (
            MergeAssignment(values={"x": 0.0, "y": 1.0}),
        )
        assert all(assignment_satisfies_mu(problem, winner) for winner in result.winners)

    def test_invalid_cel_constraint_fails_explicitly(self):
        problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 1.0, "y": 1.0}),
                ),
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
            solve_ic_merge(problem)

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
        problem = ICMergeProblem(
            concept_ids=("task",),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"task": "speech"}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"task": "yodel"}),
                ),
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

        result = solve_ic_merge(problem)

        assert result.winners == (
            MergeAssignment(values={"task": "yodel"}),
        )

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
        problem = ICMergeProblem(
            concept_ids=("task",),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"task": "speech"}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"task": "singing"}),
                ),
                MergeSource(
                    source_id="s3",
                    assignment=MergeAssignment(values={"task": "yodel"}),
                ),
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

        result = solve_ic_merge(problem)

        assert result.admissible_count == 2
        assert all(
            winner.value_for("task") in {"singing", "yodel"}
            for winner in result.winners
        )

    def test_duplicate_production_cel_runtime_is_removed(self):
        assert not hasattr(ic_merge_module, "_eval_cel_ast")
        assert not hasattr(ic_merge_module, "_eval_cel_constraint_bruteforce")

    def test_cel_constraints_reuse_one_solver_per_problem(self, monkeypatch):
        import propstore.z3_conditions as z3_conditions

        real_solver = z3_conditions.Z3ConditionSolver
        init_count = 0

        class CountingSolver(real_solver):
            def __init__(self, registry):
                nonlocal init_count
                init_count += 1
                super().__init__(registry)

        problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 1.0}),
                ),
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

        monkeypatch.setattr(z3_conditions, "Z3ConditionSolver", CountingSolver)
        result = solve_ic_merge(problem)

        assert result.winners
        assert init_count == 1

    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_always_true_cel_constraint_preserves_winners(
        self,
        source_pairs,
        operator,
    ):
        sources = tuple(
            MergeSource(
                source_id=f"s{index}",
                assignment=MergeAssignment(values={"x": x, "y": y}),
            )
            for index, (x, y) in enumerate(source_pairs)
        )
        unconstrained = solve_ic_merge(
            ICMergeProblem(
                concept_ids=("x", "y"),
                sources=sources,
                operator=operator,
            )
        )
        constrained = solve_ic_merge(
            ICMergeProblem(
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

    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_unsatisfiable_cel_constraint_yields_no_winners(
        self,
        source_pairs,
        operator,
    ):
        result = solve_ic_merge(
            ICMergeProblem(
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

    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.integers(min_value=0, max_value=4),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_z3_and_bruteforce_cel_agree_on_bounded_cases(
        self,
        source_pairs,
        limit,
    ):
        problem = ICMergeProblem(
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

    def test_cross_concept_constraint_changes_winner_set_vs_independent_solves(self):
        global_problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 1.0}),
                ),
                MergeSource(
                    source_id="s3",
                    assignment=MergeAssignment(values={"x": 1.0, "y": 0.0}),
                ),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={
                        "predicate": lambda values: values["x"] + values["y"] == 1.0,
                    },
                    description="x and y must sum to exactly 1",
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        unconstrained_x = solve_ic_merge(
            _scalar_profile_problem(
                {"s1": 0.0, "s2": 0.0, "s3": 1.0},
                operator=MergeOperator.SIGMA,
                concept_id="x",
            )
        )
        unconstrained_y = solve_ic_merge(
            _scalar_profile_problem(
                {"s1": 0.0, "s2": 1.0, "s3": 0.0},
                operator=MergeOperator.SIGMA,
                concept_id="y",
            )
        )

        constrained = solve_ic_merge(global_problem)

        independent_winner = MergeAssignment(
            values={
                "x": unconstrained_x.winners[0].value_for("x"),
                "y": unconstrained_y.winners[0].value_for("y"),
            }
        )
        assert independent_winner == MergeAssignment(values={"x": 0.0, "y": 0.0})
        assert not assignment_satisfies_mu(global_problem, independent_winner)
        assert constrained.winners == (
            MergeAssignment(values={"x": 0.0, "y": 1.0}),
            MergeAssignment(values={"x": 1.0, "y": 0.0}),
        )

    def test_custom_constraint_is_scoped_to_declared_concepts(self):
        problem = ICMergeProblem(
            concept_ids=("x", "y", "z"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0, "y": 0, "z": 0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 1, "y": 1, "z": 1}),
                ),
            ),
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={
                        "predicate": lambda values: set(values) == {"x", "y"},
                    },
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_ic_merge(problem)

        assert result.winners
        assert result.admissible_count == 8

    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.integers(min_value=0, max_value=4),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_cross_concept_winners_always_satisfy_custom_mu(
        self,
        source_pairs,
        max_sum,
        operator,
    ):
        x_values = {x for x, _ in source_pairs}
        y_values = {y for _, y in source_pairs}
        assume(any(x + y <= max_sum for x, y in product(x_values, y_values)))

        problem = ICMergeProblem(
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
                    kind=IntegrityConstraintKind.CUSTOM,
                    concept_ids=("x", "y"),
                    metadata={
                        "predicate": lambda values, limit=max_sum: values["x"] + values["y"] <= limit,
                    },
                    description="sum-bounded cross-concept admissibility",
                ),
            ),
            operator=operator,
        )

        result = solve_ic_merge(problem)

        assert result.winners
        assert all(assignment_satisfies_mu(problem, winner) for winner in result.winners)

    @given(
        st.sets(st.integers(min_value=0, max_value=2), min_size=1, max_size=3),
        st.sets(st.integers(min_value=0, max_value=2), min_size=1, max_size=3),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_separable_constraints_factorize_across_concepts(
        self,
        x_domain,
        y_domain,
        operator,
    ):
        source_pairs = list(product(sorted(x_domain), sorted(y_domain)))
        x_profile = {f"x{index}": x for index, x in enumerate(sorted(x_domain))}
        y_profile = {f"y{index}": y for index, y in enumerate(sorted(y_domain))}
        x_values = sorted(set(x_profile.values()))
        y_values = sorted(set(y_profile.values()))
        x_upper = x_values[min(len(x_values) - 1, len(x_values) // 2)]
        y_upper = y_values[min(len(y_values) - 1, len(y_values) // 2)]

        global_problem = ICMergeProblem(
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

        x_result = solve_ic_merge(
            _scalar_profile_problem(
                x_profile,
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
        y_result = solve_ic_merge(
            _scalar_profile_problem(
                y_profile,
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

        global_result = solve_ic_merge(global_problem)
        expected_winners = tuple(
            MergeAssignment(values={"x": x_assignment.value_for("x"), "y": y_assignment.value_for("y")})
            for x_assignment, y_assignment in product(x_result.winners, y_result.winners)
        )

        assert global_result.winners == expected_winners

    def test_two_concept_problem_returns_assignment_winner(self):
        problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=(
                MergeSource(
                    source_id="s1",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 0.0}),
                ),
                MergeSource(
                    source_id="s2",
                    assignment=MergeAssignment(values={"x": 0.0, "y": 1.0}),
                ),
                MergeSource(
                    source_id="s3",
                    assignment=MergeAssignment(values={"x": 1.0, "y": 1.0}),
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve_ic_merge(problem)

        assert result.winners == (
            MergeAssignment(values={"x": 0.0, "y": 1.0}),
        )
        assert result.scored_candidates[0].assignment == MergeAssignment(
            values={"x": 0.0, "y": 1.0}
        )

    def test_problem_rejects_source_assignment_outside_declared_concepts(self):
        with pytest.raises(ValueError, match="unknown concept ids"):
            ICMergeProblem(
                concept_ids=("x", "y"),
                sources=(
                    MergeSource(
                        source_id="s1",
                        assignment=MergeAssignment(values={"x": 0.0, "z": 1.0}),
                    ),
                ),
                operator=MergeOperator.SIGMA,
            )

    def test_problem_rejects_duplicate_concept_ids(self):
        with pytest.raises(ValueError, match="duplicate concept ids"):
            ICMergeProblem(
                concept_ids=("x", "x"),
                sources=(
                    MergeSource(
                        source_id="s1",
                        assignment=MergeAssignment(values={"x": 0.0}),
                    ),
                ),
                operator=MergeOperator.SIGMA,
            )

    @given(
        st.lists(
            st.tuples(st_small_assignment_value, st_small_assignment_value),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_multiconcept_source_order_does_not_change_winners(
        self,
        source_pairs,
        operator,
    ):
        forward_problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=tuple(
                MergeSource(
                    source_id=f"s{index}",
                    assignment=MergeAssignment(values={"x": x, "y": y}),
                )
                for index, (x, y) in enumerate(source_pairs)
            ),
            operator=operator,
        )
        reversed_problem = ICMergeProblem(
            concept_ids=("x", "y"),
            sources=tuple(
                MergeSource(
                    source_id=f"r{index}",
                    assignment=MergeAssignment(values={"x": x, "y": y}),
                )
                for index, (x, y) in enumerate(reversed(source_pairs))
            ),
            operator=operator,
        )

        forward_result = solve_ic_merge(forward_problem)
        reversed_result = solve_ic_merge(reversed_problem)

        assert forward_result.winners == reversed_result.winners
        assert [
            (dict(item.assignment.values), item.score)
            for item in forward_result.scored_candidates
        ] == [
            (dict(item.assignment.values), item.score)
            for item in reversed_result.scored_candidates
        ]

    def test_range_constraint_filters_admissible_winners(self):
        profile = {"b1": 5.0, "b2": 10.0, "b3": 50.0}
        problem = _scalar_profile_problem(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": 0.0, "upper": 20.0},
                ),
            ),
        )

        result = solve_ic_merge(problem)

        assert [winner.value_for("__value__") for winner in result.winners] == [10.0]
        assert result.admissible_count == 2

    def test_category_constraint_rejects_non_member_values(self):
        profile = {"b1": "speech", "b2": "whisper", "b3": "song"}
        problem = _scalar_profile_problem(
            profile,
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

        result = solve_ic_merge(problem)

        assert all(
            winner.value_for("__value__") in {"speech", "whisper"}
            for winner in result.winners
        )
        assert result.admissible_count == 2

    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_unconstrained_single_concept_matches_scalar_dispatch(self, profile, operator):
        problem = _scalar_profile_problem(profile, operator=operator)

        result = solve_ic_merge(problem)

        assert result.scored_candidates
        assert result.scored_candidates[0].assignment.value_for("__value__") == _scalar_ic_merge(
            profile,
            operator=operator,
        )

    @given(st_branch_profile)
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_winners_always_satisfy_range_mu(self, profile):
        ordered_values = sorted(profile.values())
        upper = ordered_values[len(ordered_values) // 2]
        problem = _scalar_profile_problem(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(
                IntegrityConstraint(
                    kind=IntegrityConstraintKind.RANGE,
                    concept_ids=("__value__",),
                    metadata={"lower": ordered_values[0], "upper": upper},
                ),
            ),
        )

        result = solve_ic_merge(problem)

        assert result.winners
        assert all(
            assignment_satisfies_mu(problem, winner)
            for winner in result.winners
        )

    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_source_renaming_does_not_change_best_assignment(self, profile, operator):
        renamed = {
            f"renamed_{index}": value
            for index, value in enumerate(profile.values())
        }

        original_result = solve_ic_merge(_scalar_profile_problem(profile, operator=operator))
        renamed_result = solve_ic_merge(_scalar_profile_problem(renamed, operator=operator))

        assert original_result.scored_candidates
        assert renamed_result.scored_candidates
        assert (
            original_result.scored_candidates[0].assignment.value_for("__value__")
            == renamed_result.scored_candidates[0].assignment.value_for("__value__")
        )


# ── Group 6: RenderPolicy Integration ──────────────────────────────


class TestRenderPolicyIntegration:
    def test_render_policy_has_merge_operator(self):
        """RenderPolicy has merge_operator field with default 'sigma'.

        The merge_operator field selects which IC merge operator to use
        at render time, following the pattern of existing operator-selection
        fields like reasoning_backend.
        """
        policy = RenderPolicy()
        assert policy.merge_operator == "sigma"

    def test_render_policy_has_branch_filter(self):
        """RenderPolicy has branch_filter field, default None.

        The branch_filter controls which branches are included as sources
        in the IC merge profile.
        """
        policy = RenderPolicy()
        assert policy.branch_filter is None

    def test_resolution_strategy_has_ic_merge(self):
        """ResolutionStrategy has IC_MERGE member.

        IC merge is a new resolution strategy distinct from argumentation —
        it uses distance-based merging across multiple sources rather than
        argumentation-based winner selection.
        """
        assert ResolutionStrategy.IC_MERGE == "ic_merge"

    def test_render_policy_round_trips_merge_operator_enum(self):
        policy = RenderPolicy(merge_operator=MergeOperator.GMAX)

        restored = RenderPolicy.from_dict(policy.to_dict())

        assert restored.merge_operator == MergeOperator.GMAX


class TestPublicApiHonesty:
    def test_repo_public_api_does_not_export_world_ic_merge_entrypoints(self):
        assert not hasattr(repo_api, "solve_ic_merge")
        assert "solve_ic_merge" not in repo_api.__all__
        assert "claim_distance" not in repo_api.__all__
        assert "MergeOperator" not in repo_api.__all__
        assert "ICMergeProblem" not in repo_api.__all__
        assert "ICMergeResult" not in repo_api.__all__
        assert "scalar_profile_problem" not in repo_api.__all__
        assert "sigma_merge" not in repo_api.__all__
        assert "max_merge" not in repo_api.__all__
        assert "gmax_merge" not in repo_api.__all__
        assert "ic_merge" not in repo_api.__all__

    def test_ic_merge_module_docs_point_to_global_solver(self):
        module_doc = ic_merge_module.__doc__ or ""

        assert "solve_ic_merge" in module_doc
        assert "assignment-level" in module_doc.lower()
        assert "scalar helper" not in module_doc.lower()
        assert not hasattr(ic_merge_module, "_scalar_ic_merge")
        assert not hasattr(ic_merge_module, "_scalar_profile_problem")
        assert not hasattr(ic_merge_module, "_eval_cel_ast")
        assert not hasattr(ic_merge_module, "_eval_cel_constraint_bruteforce")

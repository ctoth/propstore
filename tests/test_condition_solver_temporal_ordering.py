from __future__ import annotations

from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions import check_condition_ir, checked_condition_set


def _registry() -> dict[str, ConceptInfo]:
    return {
        "valid_from": ConceptInfo(
            id="ps:concept:valid-from",
            canonical_name="valid_from",
            kind=KindType.TIMEPOINT,
        ),
        "valid_until": ConceptInfo(
            id="ps:concept:valid-until",
            canonical_name="valid_until",
            kind=KindType.TIMEPOINT,
        ),
    }


def _condition_set(*sources: str):
    registry = _registry()
    return checked_condition_set(check_condition_ir(source, registry) for source in sources)


def test_condition_solver_applies_timepoint_interval_ordering_to_satisfaction() -> None:
    from propstore.core.conditions.solver import ConditionSolver, SolverUnsat

    solver = ConditionSolver(_registry())
    result = solver.is_condition_satisfied_result(
        check_condition_ir("valid_from <= valid_until", _registry()),
        {"valid_from": 300, "valid_until": 100},
    )

    assert isinstance(result, SolverUnsat)


def test_condition_solver_applies_timepoint_interval_ordering_to_disjointness() -> None:
    from propstore.core.conditions.solver import ConditionSolver, SolverUnsat

    solver = ConditionSolver(_registry())

    assert isinstance(
        solver.are_disjoint_result(
            _condition_set("valid_from > valid_until"),
            _condition_set("valid_from >= 0"),
        ),
        SolverUnsat,
    )


def test_condition_solver_applies_timepoint_interval_ordering_to_equivalence() -> None:
    from propstore.core.conditions.solver import ConditionSolver

    solver = ConditionSolver(_registry())

    assert solver.are_equivalent(
        _condition_set("valid_from > valid_until"),
        _condition_set("valid_until < valid_from"),
    )


def test_condition_solver_applies_timepoint_interval_ordering_to_implication() -> None:
    from propstore.core.conditions.solver import ConditionSolver

    solver = ConditionSolver(_registry())

    assert solver.implies(
        _condition_set("valid_from >= valid_until"),
        _condition_set("valid_from == valid_until"),
    )

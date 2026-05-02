from __future__ import annotations

import pytest

from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions import check_condition_ir, checked_condition_set


def _registry() -> dict[str, ConceptInfo]:
    return {
        "fundamental_frequency": ConceptInfo(
            id="ps:concept:fundamental-frequency",
            canonical_name="fundamental_frequency",
            kind=KindType.QUANTITY,
        ),
        "subglottal_pressure": ConceptInfo(
            id="ps:concept:subglottal-pressure",
            canonical_name="subglottal_pressure",
            kind=KindType.QUANTITY,
        ),
        "task": ConceptInfo(
            id="ps:concept:task",
            canonical_name="task",
            kind=KindType.CATEGORY,
            category_values=["speech", "singing", "whisper"],
            category_extensible=True,
        ),
        "closed_task": ConceptInfo(
            id="ps:concept:closed-task",
            canonical_name="closed_task",
            kind=KindType.CATEGORY,
            category_values=["speech", "singing"],
            category_extensible=False,
        ),
        "voiced": ConceptInfo(
            id="ps:concept:voiced",
            canonical_name="voiced",
            kind=KindType.BOOLEAN,
        ),
    }


def _condition_set(*sources: str):
    registry = _registry()
    return checked_condition_set(check_condition_ir(source, registry) for source in sources)


def test_condition_solver_classifies_numeric_disjointness_and_overlap() -> None:
    from propstore.core.conditions.solver import ConditionSolver

    solver = ConditionSolver(_registry())

    assert solver.are_disjoint(
        _condition_set("fundamental_frequency < 100"),
        _condition_set("fundamental_frequency > 200"),
    )
    assert not solver.are_disjoint(
        _condition_set("fundamental_frequency > 100"),
        _condition_set("fundamental_frequency > 200"),
    )


def test_condition_solver_preserves_open_category_string_semantics() -> None:
    from propstore.core.conditions.solver import ConditionSolver

    solver = ConditionSolver(_registry())

    assert solver.are_disjoint(
        _condition_set("task == 'dancing'"),
        _condition_set("task == 'speech'"),
    )
    assert not solver.are_equivalent(
        _condition_set("task != 'speech'"),
        _condition_set("task in ['singing', 'whisper']"),
    )


def test_condition_solver_rejects_unknown_closed_category_literal() -> None:
    from propstore.core.conditions.solver import ConditionSolver, Z3TranslationError

    solver = ConditionSolver(_registry())
    checked = check_condition_ir("closed_task == 'speech'", _registry())

    with pytest.raises(Z3TranslationError, match="Unknown category value"):
        solver.is_condition_satisfied(checked, {"closed_task": "dancing"})


def test_condition_solver_boolean_equivalence_implication_and_partitioning() -> None:
    from propstore.core.conditions.solver import ConditionSolver

    solver = ConditionSolver(_registry())
    voiced = _condition_set("voiced == true")
    not_not_voiced = _condition_set("!!voiced")
    unvoiced = _condition_set("voiced == false")

    assert solver.are_equivalent(voiced, not_not_voiced)
    assert solver.implies(voiced, _condition_set("voiced == true || task == 'speech'"))
    assert solver.are_disjoint(voiced, unvoiced)
    assert solver.partition_equivalence_classes([voiced, not_not_voiced, unvoiced]) == [
        [0, 1],
        [2],
    ]


def test_condition_solver_preserves_unknown_result_surface() -> None:
    from propstore.core.conditions.solver import (
        ConditionSolver,
        SolverUnknown,
        Z3UnknownError,
    )

    solver = ConditionSolver(_registry(), timeout_ms=1)
    result = solver.are_disjoint_result(
        _condition_set("fundamental_frequency * subglottal_pressure > 1"),
        _condition_set("fundamental_frequency * subglottal_pressure < -1"),
    )

    if isinstance(result, SolverUnknown):
        with pytest.raises(Z3UnknownError):
            solver.are_disjoint(
                _condition_set("fundamental_frequency * subglottal_pressure > 1"),
                _condition_set("fundamental_frequency * subglottal_pressure < -1"),
            )


def test_condition_solver_rejects_registry_fingerprint_mismatch() -> None:
    from dataclasses import replace

    from propstore.core.conditions.solver import ConditionSolver, Z3TranslationError

    condition = check_condition_ir("task == 'speech'", _registry())
    mismatched = checked_condition_set(
        (replace(condition, registry_fingerprint="sha256:not-the-registry"),)
    )

    with pytest.raises(Z3TranslationError, match="different .* registry"):
        ConditionSolver(_registry()).are_disjoint(
            mismatched,
            _condition_set("task == 'singing'"),
        )

"""Tests for condition classification semantics and exception handling."""
from unittest.mock import patch

import pytest
from propstore.condition_classifier import _try_z3_classify
from propstore.conflict_detector.models import ConflictClass


def _make_registry():
    """Minimal CEL registry for testing."""
    from propstore.cel_checker import ConceptInfo, KindType
    return {"freq": ConceptInfo(id="freq", canonical_name="freq", kind=KindType.QUANTITY)}


def _make_open_category_registry():
    from propstore.cel_checker import ConceptInfo, KindType

    return {
        "task": ConceptInfo(
            id="task",
            canonical_name="task",
            kind=KindType.CATEGORY,
            category_values=["speech", "singing"],
            category_extensible=True,
        )
    }


class TestConditionClassificationSemantics:
    def test_open_category_undeclared_literals_are_disjoint(self):
        from propstore.z3_conditions import Z3ConditionSolver

        registry = _make_open_category_registry()
        solver = Z3ConditionSolver(registry)

        result = _try_z3_classify(
            ["task == 'yodel'"],
            ["task == 'speech'"],
            registry,
            solver=solver,
        )

        assert result == ConflictClass.PHI_NODE

    def test_unknown_name_remains_hard_error(self):
        from propstore.z3_conditions import Z3ConditionSolver, Z3TranslationError

        registry = _make_open_category_registry()
        solver = Z3ConditionSolver(registry)

        with pytest.raises(Z3TranslationError, match="Undefined concept|Unknown concept"):
            _try_z3_classify(
                ["missing == 'yodel'"],
                ["task == 'speech'"],
                registry,
                solver=solver,
            )


class TestZ3ExceptionHandling:
    def test_z3_translation_error_propagates(self):
        """Z3TranslationError should propagate; there is no fallback path."""
        from propstore.z3_conditions import Z3TranslationError, Z3ConditionSolver
        registry = _make_registry()
        solver = Z3ConditionSolver(registry)
        with patch.object(solver, 'are_equivalent_result', side_effect=Z3TranslationError("test")):
            with pytest.raises(Z3TranslationError, match="test"):
                _try_z3_classify(["freq > 100"], ["freq > 200"], registry, solver=solver)

    def test_unexpected_error_propagates(self):
        """RuntimeError should NOT be caught — must propagate."""
        from propstore.z3_conditions import Z3ConditionSolver
        registry = _make_registry()
        solver = Z3ConditionSolver(registry)
        with patch.object(solver, 'are_equivalent_result', side_effect=RuntimeError("unexpected")):
            with pytest.raises(RuntimeError, match="unexpected"):
                _try_z3_classify(["freq > 100"], ["freq > 200"], registry, solver=solver)

"""Tests for condition_classifier exception handling."""
from unittest.mock import patch
import pytest
from propstore.condition_classifier import _try_z3_classify
from propstore.conflict_detector.models import ConflictClass


def _make_registry():
    """Minimal CEL registry for testing."""
    from propstore.cel_checker import ConceptInfo, KindType
    return {"freq": ConceptInfo(id="freq", canonical_name="freq", kind=KindType.QUANTITY)}


class TestZ3ExceptionHandling:
    def test_z3_translation_error_propagates(self):
        """Z3TranslationError should propagate; there is no fallback path."""
        from propstore.z3_conditions import Z3TranslationError, Z3ConditionSolver
        registry = _make_registry()
        solver = Z3ConditionSolver(registry)
        with patch.object(solver, 'are_equivalent', side_effect=Z3TranslationError("test")):
            with pytest.raises(Z3TranslationError, match="test"):
                _try_z3_classify(["freq > 100"], ["freq > 200"], registry, solver=solver)

    def test_unexpected_error_propagates(self):
        """RuntimeError should NOT be caught — must propagate."""
        from propstore.z3_conditions import Z3ConditionSolver
        registry = _make_registry()
        solver = Z3ConditionSolver(registry)
        with patch.object(solver, 'are_equivalent', side_effect=RuntimeError("unexpected")):
            with pytest.raises(RuntimeError, match="unexpected"):
                _try_z3_classify(["freq > 100"], ["freq > 200"], registry, solver=solver)

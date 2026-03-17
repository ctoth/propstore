"""Tests for the shared SymPy evaluation helper."""

from propstore.propagation import evaluate_parameterization


class TestEvaluateParameterization:
    def test_simple_expression(self):
        result = evaluate_parameterization("a + b", {"a": 1.0, "b": 2.0}, "output")
        assert result == 3.0

    def test_equality_solve(self):
        result = evaluate_parameterization(
            "Eq(y, a + b)", {"a": 1.0, "b": 2.0}, "y"
        )
        assert result == 3.0

    def test_missing_input(self):
        result = evaluate_parameterization("a + b", {"a": 1.0}, "output")
        assert result is None

    def test_division(self):
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)", {"ta": 0.5, "T0": 2.0}, "ra"
        )
        assert result == 0.25

    def test_self_referencing(self):
        """Output concept in inputs is excluded and solved correctly."""
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)",
            {"ra": 999.0, "ta": 0.5, "T0": 2.0},
            "ra",
        )
        assert result == 0.25

    def test_division_by_zero(self):
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)", {"ta": 0.5, "T0": 0.0}, "ra"
        )
        # SymPy may return zoo or None
        assert result is None or result != result  # NaN check

    def test_multiplication(self):
        result = evaluate_parameterization(
            "Eq(y, a * b)", {"a": 3.0, "b": 4.0}, "y"
        )
        assert result == 12.0

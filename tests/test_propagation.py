"""Tests for the shared SymPy evaluation helper."""

from propstore.propagation import (
    ParameterizationEvaluationStatus,
    evaluate_parameterization,
)


class TestEvaluateParameterization:
    def test_simple_expression(self):
        result = evaluate_parameterization("a + b", {"a": 1.0, "b": 2.0}, "output")
        assert result.status is ParameterizationEvaluationStatus.VALUE
        assert result.value == 3.0

    def test_equality_solve(self):
        result = evaluate_parameterization(
            "Eq(y, a + b)", {"a": 1.0, "b": 2.0}, "y"
        )
        assert result.status is ParameterizationEvaluationStatus.VALUE
        assert result.value == 3.0

    def test_missing_input(self):
        result = evaluate_parameterization("a + b", {"a": 1.0}, "output")
        assert result.status is ParameterizationEvaluationStatus.MISSING_INPUT
        assert result.value is None

    def test_division(self):
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)", {"ta": 0.5, "T0": 2.0}, "ra"
        )
        assert result.status is ParameterizationEvaluationStatus.VALUE
        assert result.value == 0.25

    def test_self_referencing(self):
        """Output concept in inputs is excluded and solved correctly."""
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)",
            {"ra": 999.0, "ta": 0.5, "T0": 2.0},
            "ra",
        )
        assert result.status is ParameterizationEvaluationStatus.VALUE
        assert result.value == 0.25

    def test_division_by_zero(self):
        result = evaluate_parameterization(
            "Eq(ra, ta / T0)", {"ta": 0.5, "T0": 0.0}, "ra"
        )
        assert result.status is ParameterizationEvaluationStatus.NO_SOLUTION
        assert result.value is None

    def test_multiplication(self):
        result = evaluate_parameterization(
            "Eq(y, a * b)", {"a": 3.0, "b": 4.0}, "y"
        )
        assert result.status is ParameterizationEvaluationStatus.VALUE
        assert result.value == 12.0

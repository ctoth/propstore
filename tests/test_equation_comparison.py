from __future__ import annotations

from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable
from propstore.equation_comparison import (
    EquationFailure,
    EquationFailureCode,
    EquationNormalization,
    canonicalize_equation,
    equation_signature,
)


def _make_equation_claim(
    *,
    expression: str | None = None,
    sympy: str | None = None,
    variables: tuple[ConflictClaimVariable, ...] | None = None,
) -> ConflictClaim:
    resolved_variables: tuple[ConflictClaimVariable, ...]
    if variables is None:
        resolved_variables = (
            ConflictClaimVariable(concept_id="length", symbol="x", role="dependent"),
            ConflictClaimVariable(concept_id="time", symbol="y", role="independent"),
        )
    else:
        resolved_variables = variables
    return ConflictClaim(
        claim_id="eq1",
        claim_type="equation",
        expression=expression,
        sympy=sympy,
        variables=resolved_variables,
    )


class TestEquationSignature:
    def test_signature_uses_typed_variables(self):
        claim = _make_equation_claim()
        assert equation_signature(claim) == ("length", ("time",))


class TestCanonicalizeEquation:
    def test_supported_equation_returns_typed_normalization(self):
        result = canonicalize_equation(_make_equation_claim(expression="x = 2*y"))

        assert isinstance(result, EquationNormalization)
        assert result.canonical == "length - 2*time"

    def test_missing_variables_is_explicit_failure(self):
        result = canonicalize_equation(_make_equation_claim(expression="x = 2*y", variables=()))

        assert result == EquationFailure(
            code=EquationFailureCode.MISSING_VARIABLES,
            detail="equation claim has no declared symbol bindings",
        )

    def test_missing_equation_text_is_explicit_failure(self):
        result = canonicalize_equation(_make_equation_claim(expression=None, sympy=None))

        assert result == EquationFailure(
            code=EquationFailureCode.MISSING_EQUATION_TEXT,
            detail="equation claim has neither expression nor sympy text",
        )

    def test_unknown_symbol_is_explicit_failure(self):
        result = canonicalize_equation(_make_equation_claim(expression="x = 2*z"))

        assert result == EquationFailure(
            code=EquationFailureCode.UNKNOWN_SYMBOL,
            detail="unknown symbol: z",
        )

    def test_double_equals_is_invalid_relation(self):
        result = canonicalize_equation(_make_equation_claim(expression="x == 2*y"))

        assert result == EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )

    def test_inequality_is_invalid_relation(self):
        result = canonicalize_equation(_make_equation_claim(expression="x <= 2*y"))

        assert result == EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )

    def test_chained_equality_is_invalid_relation(self):
        result = canonicalize_equation(_make_equation_claim(expression="x = y = 2"))

        assert result == EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )

    def test_raw_sympy_eq_text_is_not_executable_input(self):
        result = canonicalize_equation(_make_equation_claim(expression=None, sympy="Eq(x, 2*y)"))

        assert result == EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )

    def test_unsupported_function_surface_is_explicit(self):
        result = canonicalize_equation(_make_equation_claim(expression="x = And(y, y)"))

        assert result == EquationFailure(
            code=EquationFailureCode.UNSUPPORTED_SURFACE,
            detail="unsupported function: And",
        )

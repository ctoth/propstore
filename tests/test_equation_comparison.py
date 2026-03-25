"""Red-phase tests for equation_comparison parse_expr safety.

Audit finding C4: ``parse_expr`` at equation_comparison.py:76,90 accepts
arbitrary input with no transformation restrictions.  ``parse_expr`` can
execute arbitrary Python code if a malicious string is passed.

These tests verify that injection attempts are either rejected (raise)
or neutralised (return None).  The tests may or may not fail depending
on how SymPy handles the specific payloads — the point is to document
and pin the behaviour.
"""

from __future__ import annotations

import pytest

from propstore.equation_comparison import canonicalize_equation


# ── helpers ──────────────────────────────────────────────────────────


def _make_equation_claim(*, sympy: str | None = None, expression: str | None = None) -> dict:
    """Build a minimal equation claim dict with one symbol."""
    claim: dict = {
        "variables": [
            {"symbol": "x", "concept": "length", "role": "dependent"},
            {"symbol": "y", "concept": "time", "role": "independent"},
        ],
    }
    if sympy is not None:
        claim["sympy"] = sympy
    if expression is not None:
        claim["expression"] = expression
    return claim


# ── Test 1: __import__ injection via sympy field ─────────────────────


class TestParseExprSafety:
    """C4 — equation_comparison.py uses parse_expr with no restrictions."""

    def test_import_injection_via_sympy_field_is_blocked(self):
        """Passing __import__('os') in the sympy field must not execute it.

        Expected safe behaviour: raise an error OR return None.
        Must NOT: silently execute the import and return a result.
        """
        claim = _make_equation_claim(
            sympy="__import__('os').system('echo pwned')",
        )
        # If parse_expr is unrestricted, this could execute the import.
        # We want either None (parse failure) or an exception — but
        # crucially, the import must not succeed.
        try:
            result = canonicalize_equation(claim)
        except Exception:
            # Any exception is acceptable — it means the injection was
            # caught rather than executed.
            return

        # If we get here, parse_expr returned something without raising.
        # That's only OK if it returned None (i.e., it didn't parse the
        # malicious string as valid).
        assert result is None, (
            f"parse_expr returned a non-None result for an injection "
            f"payload: {result!r} — this suggests the code was executed"
        )

    def test_import_injection_via_expression_field_is_blocked(self):
        """Passing __import__ in the expression field (lhs=rhs split path)."""
        claim = _make_equation_claim(
            expression="__import__('os').system('echo pwned') = 0",
        )
        try:
            result = canonicalize_equation(claim)
        except Exception:
            return

        assert result is None, (
            f"parse_expr returned a non-None result for an injection "
            f"payload via expression field: {result!r}"
        )

    def test_eval_injection_via_sympy_field(self):
        """eval() call embedded in sympy field."""
        claim = _make_equation_claim(
            sympy="eval('1+1')",
        )
        try:
            result = canonicalize_equation(claim)
        except Exception:
            return

        assert result is None, (
            f"parse_expr returned a non-None result for eval() injection: {result!r}"
        )

    def test_exec_injection_via_sympy_field(self):
        """exec() call embedded in sympy field."""
        claim = _make_equation_claim(
            sympy="exec('import os')",
        )
        try:
            result = canonicalize_equation(claim)
        except Exception:
            return

        assert result is None, (
            f"parse_expr returned a non-None result for exec() injection: {result!r}"
        )

    def test_lambda_injection_via_sympy_field(self):
        """Lambda expression in sympy field — should not produce a callable."""
        claim = _make_equation_claim(
            sympy="(lambda: __import__('os'))()",
        )
        try:
            result = canonicalize_equation(claim)
        except Exception:
            return

        assert result is None, (
            f"parse_expr returned a non-None result for lambda injection: {result!r}"
        )

    def test_normal_equation_still_works(self):
        """Sanity check: a legitimate equation still canonicalises correctly."""
        claim = _make_equation_claim(sympy="Eq(x, 2*y)")
        result = canonicalize_equation(claim)
        assert result is not None, "legitimate equation should canonicalize"

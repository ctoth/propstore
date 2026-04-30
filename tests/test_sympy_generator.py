"""Tests for sympy_generator module.

Tests auto-generation of SymPy expressions from human-readable math strings,
and symbol validation against variable bindings.
"""

import pytest
from unittest.mock import patch

from propstore.sympy_generator import generate_sympy_rhs, check_symbols


class TestGenerateSympyRhs:
    """Tests for generate_sympy_rhs()."""

    def test_simple_equation(self):
        """Fa = 1 / (2 * pi * Ta) -> valid SymPy RHS."""
        result = generate_sympy_rhs("Fa = 1 / (2 * pi * Ta)")
        assert result is not None
        # Verify it's parseable by SymPy
        import sympy
        expr = sympy.sympify(result)
        assert expr is not None

    def test_caret_to_power(self):
        """(2*pi*Ta*f)^2 -> converts ^ to **, returns valid SymPy."""
        result = generate_sympy_rhs("(2*pi*Ta*f)^2")
        assert result is not None
        import sympy
        expr = sympy.sympify(result)
        assert expr is not None
        # Should contain ** not ^
        assert "^" not in result

    def test_unparseable_returns_none(self):
        """Unparseable garbage returns None."""
        result = generate_sympy_rhs("unparseable garbage !@#")
        assert result is None

    def test_rd_equation(self):
        """Rd = (Uo / Ee) * (F0 / 110) * 1000 -> valid SymPy with correct symbols."""
        result = generate_sympy_rhs("Rd = (Uo / Ee) * (F0 / 110) * 1000")
        assert result is not None
        import sympy
        expr = sympy.sympify(result)
        # Check that the expected free symbols are present
        symbol_names = {str(s) for s in expr.free_symbols}
        assert "Uo" in symbol_names
        assert "Ee" in symbol_names
        assert "F0" in symbol_names

    def test_simple_subtraction(self):
        """OQ = 1 - CQ -> valid SymPy."""
        result = generate_sympy_rhs("OQ = 1 - CQ")
        assert result is not None
        import sympy
        expr = sympy.sympify(result)
        symbol_names = {str(s) for s in expr.free_symbols}
        assert "CQ" in symbol_names

    def test_empty_expression_returns_none(self):
        """Empty expression returns None."""
        assert generate_sympy_rhs("") is None
        assert generate_sympy_rhs("   ") is None

    def test_expression_without_equals(self):
        """Expression without = is treated as the whole expression."""
        result = generate_sympy_rhs("x**2 + y**2")
        assert result is not None
        import sympy
        expr = sympy.sympify(result)
        symbol_names = {str(s) for s in expr.free_symbols}
        assert "x" in symbol_names
        assert "y" in symbol_names

    def test_none_input_returns_none(self):
        """None input returns None."""
        assert generate_sympy_rhs(None) is None

    def test_unexpected_parse_runtime_error_propagates(self):
        from propstore.sympy_generator import generate_sympy_rhs_with_error

        with patch(
            "propstore.sympy_generator.parse_expr",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                generate_sympy_rhs_with_error("x + 1")


class TestCheckSymbols:
    """Tests for check_symbols()."""

    def test_matching_symbols_no_warnings(self):
        """When all symbols are in the variables list, no warnings."""
        variables = [
            {"symbol": "Uo", "concept": "c1"},
            {"symbol": "Ee", "concept": "c2"},
            {"symbol": "F0", "concept": "c3"},
        ]
        warnings = check_symbols("Rd = (Uo / Ee) * (F0 / 110) * 1000", variables)
        assert warnings == []

    def test_extra_symbol_produces_warning(self):
        """Symbol in expression not in variables list -> warning."""
        variables = [
            {"symbol": "Uo", "concept": "c1"},
            {"symbol": "Ee", "concept": "c2"},
        ]
        warnings = check_symbols("Rd = (Uo / Ee) * (F0 / 110) * 1000", variables)
        assert len(warnings) >= 1
        # Should mention F0 as unbound
        assert any("F0" in w for w in warnings)

    def test_unparseable_expression_returns_empty(self):
        """If expression can't be parsed, return empty list (no crash)."""
        warnings = check_symbols("garbage !@#", [])
        assert warnings == []

    def test_empty_variables_list(self):
        """With empty variables list, all symbols produce warnings."""
        warnings = check_symbols("x + y", [])
        assert len(warnings) >= 2

    def test_constants_not_warned(self):
        """Common math constants (pi, e, E) should not produce warnings."""
        variables = [{"symbol": "Ta", "concept": "c1"}]
        warnings = check_symbols("1 / (2 * pi * Ta)", variables)
        # pi should not be warned about
        assert not any("pi" in w for w in warnings)

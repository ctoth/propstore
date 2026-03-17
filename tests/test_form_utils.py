"""Tests for FormDefinition loading and form utility functions.

Tests the structured form representation:
- Physical forms have unit_symbol and allowed_units
- Ratio forms are dimensionless
- Category/structural forms have correct kind
- load_all_forms returns complete registry
"""

from pathlib import Path

import pytest
import yaml

from compiler.form_utils import FormDefinition, load_form, load_all_forms


@pytest.fixture
def forms_dir():
    """Return the real forms directory."""
    return Path(__file__).parent.parent / "forms"


class TestFormDefinitionLoading:
    def test_load_physical_form_has_unit_symbol(self, forms_dir):
        fd = load_form(forms_dir, "pressure")
        assert fd is not None
        assert fd.unit_symbol == "Pa"
        assert fd.allowed_units == {"Pa", "cmH2O", "hPa"}
        assert fd.is_dimensionless is False

    def test_load_frequency_form(self, forms_dir):
        fd = load_form(forms_dir, "frequency")
        assert fd is not None
        assert fd.unit_symbol == "Hz"
        assert fd.allowed_units == {"Hz"}
        assert fd.is_dimensionless is False

    def test_load_ratio_form_is_dimensionless(self, forms_dir):
        fd = load_form(forms_dir, "duration_ratio")
        assert fd is not None
        assert fd.unit_symbol is None
        assert fd.is_dimensionless is True
        assert "numerator" in fd.parameters
        assert "denominator" in fd.parameters

    def test_load_level_form(self, forms_dir):
        fd = load_form(forms_dir, "level")
        assert fd is not None
        assert fd.is_dimensionless is True

    def test_load_category_form(self, forms_dir):
        fd = load_form(forms_dir, "category")
        assert fd is not None
        from compiler.cel_checker import KindType
        assert fd.kind == KindType.CATEGORY

    def test_load_structural_form(self, forms_dir):
        fd = load_form(forms_dir, "structural")
        assert fd is not None
        from compiler.cel_checker import KindType
        assert fd.kind == KindType.STRUCTURAL

    def test_load_all_forms_returns_complete_registry(self, forms_dir):
        registry = load_all_forms(forms_dir)
        expected_names = {
            "amplitude_ratio", "category", "dimensionless_compound",
            "duration_ratio", "flow", "flow_derivative", "frequency",
            "level", "pressure", "structural", "time",
        }
        assert set(registry.keys()) == expected_names

    def test_load_nonexistent_form_returns_none(self, forms_dir):
        fd = load_form(forms_dir, "nonexistent_form_xyz")
        assert fd is None

    def test_load_dimensionless_compound_form(self, forms_dir):
        fd = load_form(forms_dir, "dimensionless_compound")
        assert fd is not None
        assert fd.is_dimensionless is True

    def test_load_time_form(self, forms_dir):
        fd = load_form(forms_dir, "time")
        assert fd is not None
        assert fd.unit_symbol == "s"
        assert fd.allowed_units == {"s"}
        assert fd.is_dimensionless is False

    def test_load_flow_form(self, forms_dir):
        fd = load_form(forms_dir, "flow")
        assert fd is not None
        assert fd.unit_symbol == "cm3/s"

    def test_load_amplitude_ratio_form(self, forms_dir):
        fd = load_form(forms_dir, "amplitude_ratio")
        assert fd is not None
        assert fd.is_dimensionless is True
        assert fd.unit_symbol is None

    def test_form_definition_name_matches(self, forms_dir):
        fd = load_form(forms_dir, "frequency")
        assert fd is not None
        assert fd.name == "frequency"

    def test_load_form_with_none_returns_none(self, forms_dir):
        fd = load_form(forms_dir, None)
        assert fd is None

    def test_load_form_with_empty_string_returns_none(self, forms_dir):
        fd = load_form(forms_dir, "")
        assert fd is None

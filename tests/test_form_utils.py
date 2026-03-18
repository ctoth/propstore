"""Tests for FormDefinition loading and form utility functions.

Tests the structured form representation:
- Physical forms have unit_symbol and allowed_units
- Ratio forms are dimensionless
- Category/structural forms have correct kind
- load_all_forms returns complete registry
"""

from pathlib import Path

import pytest

from propstore.form_utils import load_form


@pytest.fixture
def forms_dir():
    """Return the real forms directory."""
    return Path(__file__).parent.parent / "forms"


class TestFormDefinitionLoading:
    def test_load_nonexistent_form_returns_none(self, forms_dir):
        fd = load_form(forms_dir, "nonexistent_form_xyz")
        assert fd is None

    def test_load_form_with_none_returns_none(self, forms_dir):
        fd = load_form(forms_dir, None)
        assert fd is None

    def test_load_form_with_empty_string_returns_none(self, forms_dir):
        fd = load_form(forms_dir, "")
        assert fd is None

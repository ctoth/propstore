"""Tests for FormDefinition loading and form utility functions.

Tests the structured form representation:
- Physical forms have unit_symbol and allowed_units
- Ratio forms are dimensionless
- Category/structural forms have correct kind
- load_all_forms returns complete registry
- UnitConversion infrastructure and normalize_to_si / from_si
"""

import math
from pathlib import Path

import pytest
import yaml

from propstore.form_utils import (
    FormDefinition,
    UnitConversion,
    load_form,
    normalize_to_si,
    from_si,
    _form_cache,
)


@pytest.fixture
def forms_dir():
    """Return the real forms directory."""
    return Path(__file__).parent.parent / "propstore" / "_resources" / "forms"


@pytest.fixture
def freq_form(forms_dir):
    """Load the frequency form, clearing cache to get fresh conversions."""
    _form_cache.pop((str(forms_dir), "frequency"), None)
    fd = load_form(forms_dir, "frequency")
    assert fd is not None
    return fd


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


class TestUnitConversionMultiplicative:
    def test_unit_conversion_multiplicative(self, freq_form):
        """0.2 kHz -> 200.0 Hz."""
        result = normalize_to_si(0.2, "kHz", freq_form)
        assert result == pytest.approx(200.0)

    def test_unit_conversion_multiplicative_roundtrip(self, freq_form):
        """normalize then from_si gives back original value."""
        original = 0.2
        si = normalize_to_si(original, "kHz", freq_form)
        back = from_si(si, "kHz", freq_form)
        assert back == pytest.approx(original)

    def test_unit_conversion_identity(self, freq_form):
        """Hz -> Hz returns unchanged."""
        result = normalize_to_si(440.0, "Hz", freq_form)
        assert result == pytest.approx(440.0)

    def test_unit_conversion_none_unit(self, freq_form):
        """None unit returns unchanged."""
        result = normalize_to_si(440.0, None, freq_form)
        assert result == pytest.approx(440.0)

    def test_unit_conversion_unknown_unit(self, freq_form):
        """Unknown unit raises ValueError."""
        with pytest.raises(ValueError, match="Unknown unit"):
            normalize_to_si(100.0, "furlongs_per_fortnight", freq_form)

    def test_load_form_preserves_conversions(self, freq_form):
        """frequency form has kHz, MHz, GHz conversions with correct multipliers."""
        assert "kHz" in freq_form.conversions
        assert "MHz" in freq_form.conversions
        assert "GHz" in freq_form.conversions
        assert freq_form.conversions["kHz"].multiplier == pytest.approx(1000)
        assert freq_form.conversions["MHz"].multiplier == pytest.approx(1_000_000)
        assert freq_form.conversions["GHz"].multiplier == pytest.approx(1_000_000_000)
        assert freq_form.conversions["kHz"].type == "multiplicative"


class TestUnitConversionAffine:
    def test_unit_conversion_affine(self, tmp_path):
        """°C -> K: normalize_to_si(100, '°C', form) ≈ 373.15."""
        form_data = {
            "name": "temperature_test",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "K",
            "dimensions": {"Θ": 1},
            "common_alternatives": [
                {
                    "unit": "°C",
                    "type": "affine",
                    "multiplier": 1.0,
                    "offset": 273.15,
                },
            ],
        }
        form_path = tmp_path / "temperature_test.yaml"
        with open(form_path, "w") as f:
            yaml.dump(form_data, f)

        _form_cache.pop((str(tmp_path), "temperature_test"), None)
        fd = load_form(tmp_path, "temperature_test")
        assert fd is not None
        result = normalize_to_si(100.0, "°C", fd)
        assert result == pytest.approx(373.15)

        # Roundtrip
        back = from_si(result, "°C", fd)
        assert back == pytest.approx(100.0)


class TestUnitConversionLogarithmic:
    def test_unit_conversion_logarithmic(self, tmp_path):
        """dB SPL -> Pa: normalize_to_si(94, 'dB_SPL', form) ≈ 1.0."""
        form_data = {
            "name": "pressure_test",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "Pa",
            "dimensions": {"M": 1, "L": -1, "T": -2},
            "common_alternatives": [
                {
                    "unit": "dB_SPL",
                    "type": "logarithmic",
                    "base": 10.0,
                    "divisor": 20.0,
                    "reference": 0.00002,
                },
            ],
        }
        form_path = tmp_path / "pressure_test.yaml"
        with open(form_path, "w") as f:
            yaml.dump(form_data, f)

        _form_cache.pop((str(tmp_path), "pressure_test"), None)
        fd = load_form(tmp_path, "pressure_test")
        assert fd is not None
        result = normalize_to_si(94.0, "dB_SPL", fd)
        assert result == pytest.approx(1.0, rel=0.01)

        # Roundtrip
        back = from_si(result, "dB_SPL", fd)
        assert back == pytest.approx(94.0, rel=0.01)

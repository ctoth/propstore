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
    clear_form_cache,
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
        with pytest.raises(ValueError, match="Cannot convert"):
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


class TestLoadTemperatureFormHasAffineConversions:
    """Load temperature form from real YAML and verify affine conversions."""

    def test_has_celsius_affine(self, forms_dir):
        _form_cache.pop((str(forms_dir), "temperature"), None)
        fd = load_form(forms_dir, "temperature")
        assert fd is not None
        assert "°C" in fd.conversions
        assert fd.conversions["°C"].type == "affine"

    def test_has_fahrenheit_affine(self, forms_dir):
        _form_cache.pop((str(forms_dir), "temperature"), None)
        fd = load_form(forms_dir, "temperature")
        assert fd is not None
        assert "°F" in fd.conversions
        assert fd.conversions["°F"].type == "affine"

    def test_fahrenheit_roundtrip(self, forms_dir):
        """212 °F -> 373.15 K -> 212 °F."""
        _form_cache.pop((str(forms_dir), "temperature"), None)
        fd = load_form(forms_dir, "temperature")
        assert fd is not None
        si = normalize_to_si(212.0, "°F", fd)
        assert si == pytest.approx(373.15, rel=0.01)
        back = from_si(si, "°F", fd)
        assert back == pytest.approx(212.0, rel=0.01)


class TestLoadLevelFormHasLogarithmicConversions:
    """Load the sound_pressure_level form and verify logarithmic conversion."""

    def test_has_db_spl_logarithmic(self, forms_dir):
        _form_cache.pop((str(forms_dir), "sound_pressure_level"), None)
        fd = load_form(forms_dir, "sound_pressure_level")
        assert fd is not None
        assert "dB_SPL" in fd.conversions
        assert fd.conversions["dB_SPL"].type == "logarithmic"

    def test_db_spl_roundtrip(self, forms_dir):
        """94 dB SPL -> ~1.0 Pa -> 94 dB SPL."""
        _form_cache.pop((str(forms_dir), "sound_pressure_level"), None)
        fd = load_form(forms_dir, "sound_pressure_level")
        assert fd is not None
        si = normalize_to_si(94.0, "dB_SPL", fd)
        assert si == pytest.approx(1.0, rel=0.01)
        back = from_si(si, "dB_SPL", fd)
        assert back == pytest.approx(94.0, rel=0.01)


class TestPintSIPrefixes:
    """Tests that require pint's automatic SI prefix handling."""

    def test_pint_normalize_si_prefixes_automatic(self, forms_dir):
        """pint handles SI prefixes without manual common_alternatives entries."""
        _form_cache.pop((str(forms_dir), "frequency"), None)
        form = load_form(forms_dir, "frequency")
        assert form is not None
        # THz is NOT in common_alternatives but pint knows it
        result = normalize_to_si(1.5, "THz", form)
        assert result == pytest.approx(1.5e12)

    def test_pint_normalize_compound_unit(self, forms_dir):
        """pint handles compound units like kPa -> Pa."""
        _form_cache.pop((str(forms_dir), "pressure"), None)
        form = load_form(forms_dir, "pressure")
        assert form is not None
        # kPa is NOT in common_alternatives but pint knows it
        result = normalize_to_si(101.325, "kPa", form)
        assert result == pytest.approx(101325.0)


class TestFormCacheClearing:
    """Tests for cache invalidation via clear_form_cache() (F7.1).

    The _form_cache module-level dict is never cleared. Modified YAML on disk
    is never re-read. These tests verify that clear_form_cache() exists and
    works correctly. They SHOULD FAIL because clear_form_cache() does not
    exist yet.
    """

    def test_clear_form_cache_reloads_from_disk(self, tmp_path):
        """After clearing the cache, load_form re-reads from disk."""
        # Write initial form
        form_data = {
            "name": "cache_test",
            "kind": "quantity",
            "dimensionless": False,
            "unit_symbol": "m",
            "dimensions": {"L": 1},
        }
        form_path = tmp_path / "cache_test.yaml"
        with open(form_path, "w") as f:
            yaml.dump(form_data, f)

        # Load form — should be cached
        fd1 = load_form(tmp_path, "cache_test")
        assert fd1 is not None
        assert fd1.unit_symbol == "m"

        # Verify caching: second call returns same object
        fd2 = load_form(tmp_path, "cache_test")
        assert fd2 is fd1

        # Modify form on disk
        form_data["unit_symbol"] = "km"
        with open(form_path, "w") as f:
            yaml.dump(form_data, f)

        # Without clearing, stale cache is returned
        fd3 = load_form(tmp_path, "cache_test")
        assert fd3.unit_symbol == "m"  # stale!

        # Clear cache and reload — should pick up disk change
        clear_form_cache()
        fd4 = load_form(tmp_path, "cache_test")
        assert fd4 is not None
        assert fd4.unit_symbol == "km"  # fresh from disk

    def test_clear_form_cache_empties_cache_dict(self, tmp_path):
        """clear_form_cache() removes all entries from _form_cache."""
        form_data = {
            "name": "empty_test",
            "kind": "quantity",
            "dimensionless": True,
        }
        form_path = tmp_path / "empty_test.yaml"
        with open(form_path, "w") as f:
            yaml.dump(form_data, f)

        load_form(tmp_path, "empty_test")
        assert len(_form_cache) > 0

        clear_form_cache()
        assert len(_form_cache) == 0

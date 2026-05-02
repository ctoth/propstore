"""Tests for unit-aware value comparison in values_compatible()."""

from propstore.core.conditions.registry import KindType
from propstore.dimensions import UnitConversion
from propstore.form_utils import FormDefinition
from propstore.value_comparison import values_compatible


def _frequency_form() -> FormDefinition:
    """Build a frequency FormDefinition with kHz conversion (multiplier=1000)."""
    return FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        allowed_units={"Hz", "kHz"},
        conversions={
            "kHz": UnitConversion(
                unit="kHz",
                type="multiplicative",
                multiplier=1000.0,
            ),
        },
    )


def test_values_compatible_different_units_same_value():
    """200 Hz vs 0.2 kHz are the same value — should be compatible when forms provided."""
    forms = {"frequency": _frequency_form()}
    claim_a = {"value": 200, "unit": "Hz"}
    claim_b = {"value": 0.2, "unit": "kHz"}

    result = values_compatible(
        None, None,
        claim_a=claim_a,
        claim_b=claim_b,
        forms=forms,
        concept_form="frequency",
    )
    assert result is True


def test_values_compatible_different_units_different_value():
    """200 Hz vs 0.3 kHz (300 Hz) — different values, should NOT be compatible."""
    forms = {"frequency": _frequency_form()}
    claim_a = {"value": 200, "unit": "Hz"}
    claim_b = {"value": 0.3, "unit": "kHz"}

    result = values_compatible(
        None, None,
        claim_a=claim_a,
        claim_b=claim_b,
        forms=forms,
        concept_form="frequency",
    )
    assert result is False


def test_values_compatible_no_forms_fallback():
    """Without forms, raw comparison is used — 200 vs 0.2 are NOT compatible."""
    claim_a = {"value": 200, "unit": "Hz"}
    claim_b = {"value": 0.2, "unit": "kHz"}

    # No forms parameter — falls back to raw numeric comparison
    result = values_compatible(
        None, None,
        claim_a=claim_a,
        claim_b=claim_b,
    )
    # Raw comparison: 200 != 0.2, so incompatible
    assert result is False

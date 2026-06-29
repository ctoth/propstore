"""Ported from the May-16 reference: unit-aware value comparison.

``values_compatible`` normalizes claim intervals to SI before comparing when a
form and the claims' units are available, so ``200 Hz`` and ``0.2 kHz`` match.
"""

from __future__ import annotations

from condition_ir import KindType

from propstore.dimensions import UnitConversion
from propstore.families.forms import FormDefinition
from propstore.value_comparison import values_compatible


def _frequency_form() -> FormDefinition:
    return FormDefinition(
        name="frequency",
        kind=KindType.QUANTITY,
        unit_symbol="Hz",
        allowed_units=("Hz", "kHz"),
        dimensions={"T": -1},
        conversions={
            "kHz": UnitConversion(unit="kHz", type="multiplicative", multiplier=1000.0),
        },
    )


def test_values_compatible_different_units_same_value() -> None:
    forms = {"frequency": _frequency_form()}
    assert values_compatible(
        None,
        None,
        claim_a={"value": 200, "unit": "Hz"},
        claim_b={"value": 0.2, "unit": "kHz"},
        forms=forms,
        concept_form="frequency",
    )


def test_values_compatible_different_units_different_value() -> None:
    forms = {"frequency": _frequency_form()}
    assert not values_compatible(
        None,
        None,
        claim_a={"value": 200, "unit": "Hz"},
        claim_b={"value": 0.3, "unit": "kHz"},
        forms=forms,
        concept_form="frequency",
    )


def test_values_compatible_no_forms_fallback() -> None:
    # Without forms, raw numeric comparison applies: 200 != 0.2.
    assert not values_compatible(
        None,
        None,
        claim_a={"value": 200, "unit": "Hz"},
        claim_b={"value": 0.2, "unit": "kHz"},
    )

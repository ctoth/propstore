"""Ported from the May-16 reference: unit-aware value comparison.

``values_compatible`` normalizes claim intervals to SI before comparing when a
form and the claims' units are available, so ``200 Hz`` and ``0.2 kHz`` match.
"""

from __future__ import annotations

import pytest
from condition_ir import KindType

from propstore.conflict_detector.models import ConflictClaim
from propstore.dimensions import UnitConversion
from propstore.families.forms import FormDefinition
from propstore.value_comparison import values_compatible


def _claim(claim_id: str, value: float, unit: str) -> ConflictClaim:
    return ConflictClaim(claim_id=claim_id, value=value, unit=unit)


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
        claim_a=_claim("a", 200.0, "Hz"),
        claim_b=_claim("b", 0.2, "kHz"),
        forms=forms,
        concept_form="frequency",
    )


def test_values_compatible_different_units_different_value() -> None:
    forms = {"frequency": _frequency_form()}
    assert not values_compatible(
        None,
        None,
        claim_a=_claim("a", 200.0, "Hz"),
        claim_b=_claim("b", 0.3, "kHz"),
        forms=forms,
        concept_form="frequency",
    )


def test_values_compatible_no_forms_fallback() -> None:
    # Without forms, raw numeric comparison applies: 200 != 0.2.
    assert not values_compatible(
        None,
        None,
        claim_a=_claim("a", 200.0, "Hz"),
        claim_b=_claim("b", 0.2, "kHz"),
    )


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("5", 5, False),
        (True, 1, False),
        (1, 1.0, True),
        ("5", "5", True),
        (True, True, True),
    ],
)
def test_values_compatible_separates_direct_and_numeric_scalars(
    left: object,
    right: object,
    expected: bool,
) -> None:
    assert values_compatible(left, right) is expected

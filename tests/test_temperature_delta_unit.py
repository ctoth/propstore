from __future__ import annotations

from propstore import dimensions
from propstore.cel_checker import KindType
from propstore.families.forms.stages import FormDefinition


def _temperature_form() -> FormDefinition:
    return FormDefinition(
        name="temperature",
        kind=KindType.QUANTITY,
        unit_symbol="K",
        allowed_units={"K", "degC", "delta_degC", "delta_degF"},
        dimensions={"Theta": 1},
        conversions={
            "degC": dimensions.UnitConversion(
                unit="degC",
                type="affine",
                multiplier=1.0,
                offset=273.15,
            )
        },
        delta_conversions={
            "delta_degC": dimensions.UnitConversion(
                unit="delta_degC",
                type="multiplicative",
                multiplier=1.0,
            ),
            "delta_degF": dimensions.UnitConversion(
                unit="delta_degF",
                type="multiplicative",
                multiplier=5.0 / 9.0,
            ),
        },
    )


def test_delta_celsius_normalizes_without_absolute_temperature_offset() -> None:
    form = _temperature_form()

    assert dimensions.normalize_to_si(5.0, "delta_degC", form) == 5.0
    assert dimensions.normalize_to_si(5.0, "degC", form) == 278.15


def test_delta_fahrenheit_normalizes_without_absolute_temperature_offset() -> None:
    assert dimensions.normalize_to_si(9.0, "delta_degF", _temperature_form()) == 5.0


def test_pint_knows_delta_temperature_units() -> None:
    assert dimensions.can_convert_unit_to("delta_degC", "K")
    assert dimensions.can_convert_unit_to("delta_degF", "K")

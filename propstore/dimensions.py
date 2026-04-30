"""Physical dimension and unit conversion helpers.

This module owns Pint, SI conversion, and dimensional algebra. Semantic form
loading stays in ``propstore.families.forms``; lemon lexical forms stay in
``propstore.core.lemon.forms``.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import pint


class DimensionalForm(Protocol):
    name: str
    unit_symbol: str | None
    dimensions: dict[str, int] | None
    conversions: dict[str, "UnitConversion"]
    delta_conversions: dict[str, "UnitConversion"]


# Module-level unit registry for pint conversions.
ureg = pint.UnitRegistry()


# Map propstore unit symbols to pint-recognized names.
_PINT_ALIASES: dict[str, str] = {
    "°C": "degC",
    "°F": "degF",
    "µ": "u",
    "d": "day",
    "wk": "week",
    "mo": "month",
    "yr": "year",
}


def _pint_unit(unit_str: str) -> str:
    """Translate a propstore unit symbol to a pint-compatible name."""
    return _PINT_ALIASES.get(unit_str, unit_str)


@dataclass(frozen=True)
class UnitConversion:
    """Conversion specification from an alternative unit to a form's SI unit."""

    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


@dataclass(frozen=True)
class ExtraUnitDefinition:
    """Additional unit metadata declared on a form."""

    symbol: str
    dimensions: dict[str, int]


def normalize_to_si(value: float, unit: str | None, form: DimensionalForm) -> float:
    """Convert a value from the given unit to the form's canonical SI unit."""
    if unit is None or unit == form.unit_symbol:
        return value
    if form.unit_symbol is None:
        raise ValueError(
            f"Cannot convert '{unit}' for dimensionless form '{form.name}'"
        )
    if unit in form.delta_conversions:
        conv = form.delta_conversions[unit]
        if conv.type != "multiplicative":
            raise ValueError(
                f"Delta unit '{unit}' for form '{form.name}' must be multiplicative"
            )
        return value * conv.multiplier
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.reference * conv.base ** (value / conv.divisor)
        if conv.type == "multiplicative":
            return value * conv.multiplier
        if conv.type == "affine":
            return value * conv.multiplier + conv.offset
    try:
        q = ureg.Quantity(value, _pint_unit(unit))
        return q.to(_pint_unit(form.unit_symbol)).magnitude
    except (pint.UndefinedUnitError, pint.DimensionalityError) as exc:
        raise ValueError(
            f"Cannot convert '{unit}' to '{form.unit_symbol}' for form '{form.name}': {exc}"
        )


def from_si(si_value: float, unit: str | None, form: DimensionalForm) -> float:
    """Convert an SI value back to the given unit."""
    if unit is None or unit == form.unit_symbol:
        return si_value
    if form.unit_symbol is None:
        raise ValueError(
            f"Cannot convert to '{unit}' for dimensionless form '{form.name}'"
        )
    if unit in form.delta_conversions:
        conv = form.delta_conversions[unit]
        if conv.type != "multiplicative":
            raise ValueError(
                f"Delta unit '{unit}' for form '{form.name}' must be multiplicative"
            )
        return si_value / conv.multiplier
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.divisor * math.log(si_value / conv.reference, conv.base)
        if conv.type == "multiplicative":
            return si_value / conv.multiplier
        if conv.type == "affine":
            return (si_value - conv.offset) / conv.multiplier
    try:
        q = ureg.Quantity(si_value, _pint_unit(form.unit_symbol))
        return q.to(_pint_unit(unit)).magnitude
    except (pint.UndefinedUnitError, pint.DimensionalityError) as exc:
        raise ValueError(
            f"Cannot convert '{form.unit_symbol}' to '{unit}' for form '{form.name}': {exc}"
        )


def can_convert_unit_to(unit: str, target_unit: str | None) -> bool:
    """Return whether Pint can convert ``unit`` to ``target_unit``."""
    if target_unit is None:
        return False
    try:
        src = ureg.Quantity(1, _pint_unit(unit))
        src.to(_pint_unit(target_unit))
        return True
    except (
        pint.UndefinedUnitError,
        pint.DimensionalityError,
        TypeError,
        ValueError,
    ):
        return False


_PINT_DIMENSION_BASES = {
    "M": "kilogram",
    "L": "meter",
    "T": "second",
    "I": "ampere",
    "Theta": "kelvin",
    "N": "mole",
    "J": "candela",
}


def register_extra_unit_with_pint(symbol: str, dimensions: dict[str, int]) -> None:
    """Register a form-declared unit symbol in the module Pint registry."""
    if can_convert_unit_to(symbol, _pint_expression_for_dimensions(dimensions)):
        return
    expression = _pint_expression_for_dimensions(dimensions)
    if expression == "dimensionless":
        definition = f"{symbol} = []"
    else:
        definition = f"{symbol} = {expression}"
    try:
        ureg.define(definition)
    except pint.errors.RedefinitionError as exc:
        if can_convert_unit_to(symbol, expression):
            return
        raise ValueError(f"Unit symbol '{symbol}' is already defined incompatibly") from exc


def _pint_expression_for_dimensions(dimensions: dict[str, int]) -> str:
    factors: list[str] = []
    for key, exponent in sorted(dimensions.items()):
        if exponent == 0:
            continue
        base = _PINT_DIMENSION_BASES.get(key)
        if base is None:
            raise ValueError(f"Cannot register Pint unit for unknown dimension '{key}'")
        if exponent == 1:
            factors.append(base)
        else:
            factors.append(f"{base} ** {exponent}")
    return " * ".join(factors) if factors else "dimensionless"


def forms_with_dimensions(
    forms: Sequence[DimensionalForm | None],
) -> list[DimensionalForm] | None:
    """Filter a form list, returning None if any form lacks dimensions."""
    concrete: list[DimensionalForm] = []
    for form_def in forms:
        if form_def is None or form_def.dimensions is None:
            return None
        concrete.append(form_def)
    return concrete


def required_dimensions(form_def: DimensionalForm) -> dict[str, int]:
    """Return dimensions dict, raising ValueError if absent."""
    dimensions = form_def.dimensions
    if dimensions is None:
        raise ValueError(f"form '{form_def.name}' has no dimensions")
    return dimensions


def verify_form_algebra_dimensions(
    output: DimensionalForm,
    inputs: list[DimensionalForm],
    operation: str,
) -> bool:
    """Check dimensional consistency of a form algebra expression."""
    if output.dimensions is None:
        return False
    concrete_inputs = forms_with_dimensions(inputs)
    if concrete_inputs is None:
        return False
    try:
        import sympy as sp
        from bridgman import verify_expr

        dim_map: dict[str, dict[str, int]] = {output.name: dict(required_dimensions(output))}
        for inp_fd in concrete_inputs:
            dim_map[inp_fd.name] = dict(required_dimensions(inp_fd))

        form_parsed = sp.sympify(operation)
        if not isinstance(form_parsed, sp.Eq):
            return False
        return bool(verify_expr(form_parsed, dim_map))
    except (KeyError, ValueError, ImportError):
        return False


def dims_signature(dimensions: dict[str, int] | None) -> str | None:
    """Canonical Bridgman dimension signature."""
    if dimensions is None:
        return None
    from bridgman import dims_signature as bridgman_dims_signature

    return bridgman_dims_signature(dimensions)

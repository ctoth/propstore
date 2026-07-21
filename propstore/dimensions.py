"""Physical-dimension and unit-conversion helpers.

This module owns the things ``bridgman`` deliberately does *not*: Pint-backed
unit conversion (SI normalization, affine/logarithmic/delta scales, SI prefixes,
clinical and domain units) and the small conversion-spec value types that ride on
a physical-dimension form. The canonical *dimensional algebra* — signatures,
products, equality — stays in ``bridgman`` and is imported and called directly
(no propstore re-spelling): see :func:`product_dimensions` / :func:`dimensions_match`,
which compose ``bridgman.mul_dims`` / ``pow_dims`` / ``dims_equal``.

Pint's ``UnitRegistry`` is generic over a magnitude type that pint leaves
unparameterized, so under strict typing every direct pint expression reads as
partially unknown. We therefore confine pint to a typed :class:`_PintRegistry` /
:class:`_PintQuantity` Protocol surface and absorb the one untyped construction in
:func:`_make_registry`; nothing else in propstore touches pint.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import msgspec
import pint
from bridgman import canonicalize_dims, dims_equal, mul_dims, pow_dims


class UnitConversion(msgspec.Struct, frozen=True):
    """How to convert one alternative unit to a form's canonical (SI) unit.

    ``type`` selects the scale: ``"multiplicative"`` (``si = value * multiplier``),
    ``"affine"`` (``si = value * multiplier + offset``, e.g. degC→K), or
    ``"logarithmic"`` (``si = reference * base ** (value / divisor)``, e.g. dB).
    """

    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class ExtraUnitDefinition(msgspec.Struct, frozen=True):
    """A form-declared unit symbol and the SI dimensions it carries."""

    symbol: str
    dimensions: dict[str, int]


class DimensionalForm(Protocol):
    """The structural slice of a physical-dimension form this module reads.

    :class:`~propstore.families.forms.FormDefinition` satisfies it; the dependency
    points form→dimensions, never the reverse, so dimensions stays leaf-level.
    """

    name: str
    unit_symbol: str | None
    dimensions: dict[str, int] | None
    conversions: dict[str, UnitConversion]
    delta_conversions: dict[str, UnitConversion]


# ── Pint boundary (typed Protocol surface) ───────────────────────────────


class _PintQuantity(Protocol):
    @property
    def magnitude(self) -> float: ...
    def to(self, other: str) -> _PintQuantity: ...


class _PintRegistry(Protocol):
    def Quantity(self, value: float, units: str) -> _PintQuantity: ...
    def define(self, definition: str) -> None: ...


def _as_registry(obj: Any) -> _PintRegistry:
    """Narrow pint's partially-unknown registry to the typed Protocol surface.

    ``pint.UnitRegistry()`` is partially unknown under strict typing (its
    magnitude TypeVar is upstream-unparameterized). Passing the construction
    straight into this ``Any`` parameter is the single, honest narrowing point;
    every other pint access goes through :class:`_PintRegistry`.
    """

    return obj


# Module-level Pint registry for unit conversions.
ureg: _PintRegistry = _as_registry(pint.UnitRegistry())


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
    """Translate a propstore unit symbol to a Pint-compatible name."""

    return _PINT_ALIASES.get(unit_str, unit_str)


def normalize_to_si(value: float, unit: str | None, form: DimensionalForm) -> float:
    """Convert ``value`` (given in ``unit``) to the form's canonical SI unit."""

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
        return (
            ureg.Quantity(value, _pint_unit(unit))
            .to(_pint_unit(form.unit_symbol))
            .magnitude
        )
    except (pint.UndefinedUnitError, pint.DimensionalityError) as exc:
        raise ValueError(
            f"Cannot convert '{unit}' to '{form.unit_symbol}' for form '{form.name}': {exc}"
        ) from exc


def from_si(si_value: float, unit: str | None, form: DimensionalForm) -> float:
    """Convert an SI value back to ``unit``."""

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
            import math

            return conv.divisor * math.log(si_value / conv.reference, conv.base)
        if conv.type == "multiplicative":
            return si_value / conv.multiplier
        if conv.type == "affine":
            return (si_value - conv.offset) / conv.multiplier
    try:
        return (
            ureg.Quantity(si_value, _pint_unit(form.unit_symbol))
            .to(_pint_unit(unit))
            .magnitude
        )
    except (pint.UndefinedUnitError, pint.DimensionalityError) as exc:
        raise ValueError(
            f"Cannot convert '{form.unit_symbol}' to '{unit}' for form '{form.name}': {exc}"
        ) from exc


def can_convert_unit_to(unit: str, target_unit: str | None) -> bool:
    """Return whether Pint can convert ``unit`` to ``target_unit``."""

    if target_unit is None:
        return False
    try:
        ureg.Quantity(1.0, _pint_unit(unit)).to(_pint_unit(target_unit))
        return True
    except (pint.UndefinedUnitError, pint.DimensionalityError, TypeError, ValueError):
        return False


_PINT_DIMENSION_BASES: dict[str, str] = {
    "M": "kilogram",
    "L": "meter",
    "T": "second",
    "I": "ampere",
    "Theta": "kelvin",
    "N": "mole",
    "J": "candela",
}


def _pint_expression_for_dimensions(dimensions: dict[str, int]) -> str:
    factors: list[str] = []
    for key, exponent in sorted(dimensions.items()):
        if exponent == 0:
            continue
        base = _PINT_DIMENSION_BASES.get(key)
        if base is None:
            raise ValueError(f"Cannot register Pint unit for unknown dimension '{key}'")
        factors.append(base if exponent == 1 else f"{base} ** {exponent}")
    return " * ".join(factors) if factors else "dimensionless"


def register_extra_unit_with_pint(symbol: str, dimensions: dict[str, int]) -> None:
    """Register a form-declared unit symbol in the module Pint registry."""

    expression = _pint_expression_for_dimensions(dimensions)
    if can_convert_unit_to(symbol, expression):
        return
    definition = (
        f"{symbol} = []"
        if expression == "dimensionless"
        else f"{symbol} = {expression}"
    )
    try:
        ureg.define(definition)
    except pint.errors.RedefinitionError as exc:
        if can_convert_unit_to(symbol, expression):
            return
        raise ValueError(
            f"Unit symbol '{symbol}' is already defined incompatibly"
        ) from exc


def forms_with_dimensions(
    forms: Sequence[DimensionalForm | None],
) -> list[DimensionalForm] | None:
    """Return the forms if every one carries dimensions, else ``None``."""

    concrete: list[DimensionalForm] = []
    for form_def in forms:
        if form_def is None or form_def.dimensions is None:
            return None
        concrete.append(form_def)
    return concrete


def required_dimensions(form_def: DimensionalForm) -> dict[str, int]:
    """Return the form's dimensions, raising ``ValueError`` if absent."""

    dimensions = form_def.dimensions
    if dimensions is None:
        raise ValueError(f"form '{form_def.name}' has no dimensions")
    return dimensions


# ── Dimensional algebra (composed from bridgman, no re-spelling) ──────────


def product_dimensions(factors: Sequence[tuple[dict[str, int], int]]) -> dict[str, int]:
    """Combine ``(dimensions, exponent)`` factors into one canonical signature.

    Pure composition of ``bridgman.pow_dims`` / ``mul_dims`` / ``canonicalize_dims``
    — the dimensional algebra is bridgman's; propstore only supplies the factors.
    """

    result: dict[str, int] = {}
    for dimensions, exponent in factors:
        result = mul_dims(result, pow_dims(canonicalize_dims(dimensions), exponent))
    return canonicalize_dims(result)


def dimensions_match(
    output: dict[str, int],
    factors: Sequence[tuple[dict[str, int], int]],
) -> bool:
    """Whether ``output`` equals the dimensional product of ``factors`` (via bridgman)."""

    return dims_equal(product_dimensions(factors), canonicalize_dims(output))

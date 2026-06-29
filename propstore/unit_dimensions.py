"""Resolve unit symbols to SI dimensions.

Maps unit strings ("kPa", "Hz", "cm/s") to SI base-dimension exponents
(``{"M": 1, "L": -1, "T": -2}``). The base table is shipped as
``propstore/_resources/physgen_units.json`` (generated from ISO 80000); a form's
``extra_units`` add domain-specific symbols at registration time.

Dimensional *equality* is bridgman's (`dims_equal`) — called directly, never
re-spelled here.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Protocol

from bridgman import canonicalize_dims, dims_equal

from propstore.dimensions import ExtraUnitDefinition, register_extra_unit_with_pint
from propstore.resources import load_resource_text, resource_exists

Dimensions = dict[str, int]

_symbol_table: dict[str, Dimensions] | None = None


class _FormWithExtraUnits(Protocol):
    """The slice of a form this module reads: its declared extra units."""

    extra_units: tuple[ExtraUnitDefinition, ...]


def clear_symbol_table() -> None:
    """Reset the module symbol table, forcing a rebuild on next access."""

    global _symbol_table
    _symbol_table = None


def _get_symbol_table() -> dict[str, Dimensions]:
    """Lazily load the symbol→dimensions table from the shipped physgen JSON."""

    global _symbol_table
    if _symbol_table is not None:
        return _symbol_table
    table: dict[str, Dimensions] = {}
    if resource_exists("physgen_units.json"):
        raw: dict[str, Dimensions] = json.loads(load_resource_text("physgen_units.json"))
        for symbol, dims in raw.items():
            table[symbol] = canonicalize_dims(dims)
    _symbol_table = table
    return table


def register_form_units(forms: Iterable[_FormWithExtraUnits]) -> None:
    """Register every form's ``extra_units`` into the symbol table and Pint.

    Makes form-declared unit symbols resolvable for dimensional analysis and
    convertible via Pint.
    """

    table = _get_symbol_table()
    for form_def in forms:
        for extra in form_def.extra_units:
            dims = canonicalize_dims(extra.dimensions)
            table[extra.symbol] = dims
            register_extra_unit_with_pint(extra.symbol, dims)


def resolve_unit_dimensions(unit: str) -> Dimensions | None:
    """Resolve a unit string to its SI dimensions, or ``None`` if unrecognized."""

    table = _get_symbol_table()
    if unit in table:
        return table[unit]
    stripped = unit.strip().strip("\"'")
    if stripped in table:
        return table[stripped]
    return None


def dimensions_compatible(unit_dims: Dimensions, form_dims: Dimensions) -> bool:
    """Whether a unit's dimensions match a form's dimensions (via bridgman)."""

    return dims_equal(unit_dims, form_dims)

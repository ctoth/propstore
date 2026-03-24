"""Unit-to-dimensions resolver.

Resolves unit strings (like "kPa", "cm/s", "Hz") to their SI dimensions
(like {M: 1, L: -1, T: -2}). Used by claim validation to check that a
claim's unit is dimensionally compatible with its concept's form.

The base lookup table is shipped as propstore/_resources/physgen_units.json,
generated from physgen's ISO 80000 physics.yml. Domain-specific units
come from form YAML files via extra_units and register_form_units().
"""
from __future__ import annotations

import json
from pathlib import Path

from bridgman import dims_equal


# ── Types ────────────────────────────────────────────────────────────

Dimensions = dict[str, int]  # e.g. {"M": 1, "L": -1, "T": -2}

# physgen uses unicode Θ for temperature; form YAMLs use ascii THETA
_DIM_KEY_NORMALIZE = {"Θ": "THETA", "θ": "THETA"}

def _normalize_dim_key(k: str) -> str:
    return _DIM_KEY_NORMALIZE.get(k, k)



# ── Load shipped lookup table ────────────────────────────────────────

_symbol_table: dict[str, Dimensions] | None = None


def _get_symbol_table() -> dict[str, Dimensions]:
    """Lazy-load the symbol->dimensions table from shipped physgen JSON."""
    global _symbol_table
    if _symbol_table is not None:
        return _symbol_table

    from propstore.resources import load_resource_text, resource_exists

    table: dict[str, Dimensions] = {}

    if resource_exists("physgen_units.json"):
        raw = json.loads(load_resource_text("physgen_units.json"))
        for symbol, dims in raw.items():
            table[symbol] = {
                _normalize_dim_key(k): v for k, v in dims.items() if v != 0
            }

    _symbol_table = table
    return table


def register_form_units(forms_dir: Path) -> None:
    """Register extra_units from all form YAML files into the symbol table.

    Called during validation/build to make form-declared units available
    for dimensional analysis.
    """
    from propstore.form_utils import load_all_forms

    table = _get_symbol_table()
    for form_def in load_all_forms(forms_dir).values():
        for eu in form_def.extra_units:
            symbol = eu["symbol"]
            dims = eu.get("dimensions", {})
            if isinstance(dims, dict):
                table[symbol] = {k: int(v) for k, v in dims.items() if v != 0}
            else:
                table[symbol] = {}


# ── Public API ───────────────────────────────────────────────────────

def resolve_unit_dimensions(unit: str) -> Dimensions | None:
    """Resolve a unit string to its SI dimensions.

    Returns the dimensions dict, or None if the unit is unrecognized.

    Examples:
        resolve_unit_dimensions("Hz")   → {"T": -1}
        resolve_unit_dimensions("kPa")  → {"M": 1, "L": -1, "T": -2}
        resolve_unit_dimensions("dB")   → {}
        resolve_unit_dimensions("??")   → None
    """
    table = _get_symbol_table()

    if unit in table:
        return table[unit]

    # Try stripping quotes/whitespace
    stripped = unit.strip().strip("\"'")
    if stripped in table:
        return table[stripped]

    return None


def dimensions_compatible(unit_dims: Dimensions, form_dims: Dimensions) -> bool:
    """Check if a unit's dimensions are compatible with a form's dimensions.

    Both are dicts like {"M": 1, "L": -1, "T": -2}. Empty dict = dimensionless.
    Missing keys are treated as exponent 0.
    """
    return dims_equal(unit_dims, form_dims)

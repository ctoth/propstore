"""Unit-to-dimensions resolver.

Resolves unit strings (like "kPa", "cm/s", "Hz") to their SI dimensions
(like {M: 1, L: -1, T: -2}). Used by claim validation to check that a
claim's unit is dimensionally compatible with its concept's form.

The base lookup table is shipped as propstore/_resources/physgen_units.json,
generated from physgen's ISO 80000 physics.yml. Domain-specific units
are layered on top (currently hardcoded, migrating to form YAML).
"""
from __future__ import annotations

import json
from pathlib import Path


# ── Types ────────────────────────────────────────────────────────────

Dimensions = dict[str, int]  # e.g. {"M": 1, "L": -1, "T": -2}


# ── Common units not in physgen (domain-independent) ─────────────────

_COMMON_UNITS: dict[str, Dimensions] = {
    "ratio": {},
    "fraction": {},
    "dimensionless": {},
    "%": {},
    "count": {},
    "bits": {},
    "points": {},
    "cps": {"T": -1},   # cycles per second = Hz
    "1/s": {"T": -1},
}

# Legacy speech-specific units — loaded as fallback when no forms provide
# extra_units. Will be removed after qlatt migrates to form-based units.
_LEGACY_DOMAIN_UNITS: dict[str, Dimensions] = {
    "dB": {},
    "dB SPL": {},
    "dB/oct": {},
    "dB/octave": {},
    "dB/dB": {},
    "dB re 0.0002 dyne/cm^2": {},
    "ST": {},
    "st": {},
    "semitones": {},
    "cents": {},
    "SD": {},
    "syl/s": {"T": -1},
    "ms/syl": {"T": 1},
    "fps": {"T": -1},
    "samples": {},
    "frames": {},
    "periods": {},
    "kbps": {},
    "1–9 scale": {},
}


# ── Load shipped lookup table ────────────────────────────────────────

_symbol_table: dict[str, Dimensions] | None = None


def _get_symbol_table() -> dict[str, Dimensions]:
    """Lazy-load the symbol->dimensions table from shipped JSON + common units."""
    global _symbol_table
    if _symbol_table is not None:
        return _symbol_table

    from propstore.resources import load_resource_text, resource_exists

    table: dict[str, Dimensions] = {}

    if resource_exists("physgen_units.json"):
        raw = json.loads(load_resource_text("physgen_units.json"))
        for symbol, dims in raw.items():
            table[symbol] = {k: v for k, v in dims.items() if v != 0}

    # Layer common units on top
    table.update(_COMMON_UNITS)

    # Legacy fallback: include domain-specific units until forms provide extra_units
    table.update(_LEGACY_DOMAIN_UNITS)

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
    all_keys = set(unit_dims.keys()) | set(form_dims.keys())
    for k in all_keys:
        if unit_dims.get(k, 0) != form_dims.get(k, 0):
            return False
    return True

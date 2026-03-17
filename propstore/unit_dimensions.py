"""Unit-to-dimensions resolver.

Resolves unit strings (like "kPa", "cm/s", "Hz") to their SI dimensions
(like {M: 1, L: -1, T: -2}). Used by claim validation to check that a
claim's unit is dimensionally compatible with its concept's form.

The base lookup table is shipped as propstore/_resources/physgen_units.json,
generated from physgen's ISO 80000 physics.yml. Speech-specific units
(dB, semitones, etc.) are layered on top.
"""
from __future__ import annotations

import json


# ── Types ────────────────────────────────────────────────────────────

Dimensions = dict[str, int]  # e.g. {"M": 1, "L": -1, "T": -2}


# ── Speech-specific units not in physgen ─────────────────────────────

_SPEECH_UNITS: dict[str, Dimensions] = {
    # Level / logarithmic (dimensionless)
    "dB": {},
    "dB SPL": {},
    "dB/oct": {},
    "dB/octave": {},
    "dB/dB": {},
    "dB re 0.0002 dyne/cm^2": {},
    # Semitones (logarithmic frequency ratio)
    "ST": {},
    "st": {},
    "semitones": {},
    "cents": {},
    # Dimensionless measures
    "ratio": {},
    "fraction": {},
    "dimensionless": {},
    "SD": {},
    # Rates that physgen doesn't cover
    "cps": {"T": -1},  # cycles per second = Hz
    "syl/s": {"T": -1},
    "ms/syl": {"T": 1},
    "fps": {"T": -1},  # frames per second
    "1/s": {"T": -1},
    # Other domain units
    "samples": {},
    "frames": {},
    "points": {},
    "bits": {},
    "count": {},
    "periods": {},
    "kbps": {},
    "1–9 scale": {},
}


# ── Load shipped lookup table ────────────────────────────────────────

_symbol_table: dict[str, Dimensions] | None = None


def _get_symbol_table() -> dict[str, Dimensions]:
    """Lazy-load the symbol→dimensions table from shipped JSON + speech supplement."""
    global _symbol_table
    if _symbol_table is not None:
        return _symbol_table

    from propstore.resources import load_resource_text, resource_exists

    table: dict[str, Dimensions] = {}

    if resource_exists("physgen_units.json"):
        raw = json.loads(load_resource_text("physgen_units.json"))
        for symbol, dims in raw.items():
            table[symbol] = {k: v for k, v in dims.items() if v != 0}

    # Layer speech-specific units on top
    table.update(_SPEECH_UNITS)

    _symbol_table = table
    return table


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

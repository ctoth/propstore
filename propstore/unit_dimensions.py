"""Unit-to-dimensions resolver using physgen's physics.yml as the source of truth.

Resolves unit strings (like "kPa", "cm/s", "Hz") to their SI dimensions
(like {M: 1, L: -1, T: -2}). Used by claim validation to check that a
claim's unit is dimensionally compatible with its concept's form.

The lookup table is built from physgen's physics.yml at import time.
Speech-specific units (dB, semitones) are added as a supplement.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ── Types ────────────────────────────────────────────────────────────

Dimensions = dict[str, int]  # e.g. {"M": 1, "L": -1, "T": -2}


# ── Speech-specific units not in physgen ─────────────────────────────

# These are logarithmic or domain-specific scales that don't participate
# in standard dimensional analysis but need to be recognized.
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
    # Rates that physgen might not cover
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
    "kbps": {},  # kilobits per second (data rate, not physics)
    "1–9 scale": {},
}


# ── Physgen loader ───────────────────────────────────────────────────

def _load_physgen_units(physics_yml: Path) -> dict[str, Dimensions]:
    """Parse physgen physics.yml and build {symbol: dimensions} lookup."""
    with open(physics_yml, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    table: dict[str, Dimensions] = {}
    for scalar in spec.get("scalars", []):
        dims = scalar.get("dimensions", {})
        # Normalize: drop zero-exponent entries
        dims = {k: v for k, v in dims.items() if v != 0}

        for unit_name, unit_data in scalar.get("units", {}).items():
            if isinstance(unit_data, dict):
                symbol = unit_data.get("symbol")
            else:
                # Old format: units: {Name: factor}
                symbol = None

            if symbol and isinstance(symbol, str) and symbol.strip():
                table[symbol.strip()] = dims

    return table


# ── Build the lookup ─────────────────────────────────────────────────

_PHYSGEN_PATH = Path(__file__).resolve().parent.parent.parent / "physgen" / "example" / "physics.yml"
# Fallback: try sibling directory layout
_PHYSGEN_ALT = Path("C:/Users/Q/code/physgen/example/physics.yml")

_symbol_table: dict[str, Dimensions] | None = None


def _get_symbol_table() -> dict[str, Dimensions]:
    """Lazy-load the symbol→dimensions table."""
    global _symbol_table
    if _symbol_table is not None:
        return _symbol_table

    table: dict[str, Dimensions] = {}

    # Try to load physgen
    for path in [_PHYSGEN_PATH, _PHYSGEN_ALT]:
        if path.exists():
            table = _load_physgen_units(path)
            break

    # Layer speech-specific units on top (override physgen if conflict)
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

    # Direct lookup
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

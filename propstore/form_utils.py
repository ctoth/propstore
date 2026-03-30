"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Sequence
from typing import Any

import jsonschema
import pint
import yaml

from propstore.cel_checker import KindType
from propstore.resources import load_resource_json

# Module-level unit registry for pint conversions
ureg = pint.UnitRegistry()

# Map propstore unit symbols to pint-recognized names
_PINT_ALIASES: dict[str, str] = {"°C": "degC", "°F": "degF", "µ": "u"}


def _pint_unit(unit_str: str) -> str:
    """Translate a propstore unit symbol to a pint-compatible name."""
    return _PINT_ALIASES.get(unit_str, unit_str)



@dataclass(frozen=True)
class UnitConversion:
    """Conversion specification from an alternative unit to the form's SI unit."""
    unit: str
    type: str          # "multiplicative", "affine", "logarithmic"
    multiplier: float = 1.0
    offset: float = 0.0      # affine: si = raw * multiplier + offset
    base: float = 10.0       # logarithmic: si = reference * base^(raw / divisor)
    divisor: float = 1.0
    reference: float = 1.0


@dataclass
class FormDefinition:
    """Structured representation of a loaded form YAML file."""
    name: str
    kind: KindType
    unit_symbol: str | None = None
    allowed_units: set[str] = field(default_factory=set)
    is_dimensionless: bool = False
    parameters: dict = field(default_factory=dict)
    dimensions: dict[str, int] | None = None
    extra_units: list[dict[str, Any]] = field(default_factory=list)
    conversions: dict[str, UnitConversion] = field(default_factory=dict)


_form_cache: dict[tuple[str, str], FormDefinition | None] = {}


def clear_form_cache() -> None:
    """Clear the module-level form cache, forcing reload from disk on next access."""
    _form_cache.clear()
    # Also clear schema cache if it exists
    global _form_schema_cache
    _form_schema_cache = None


_KIND_MAP = {
    "quantity": KindType.QUANTITY,
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
}


def parse_form(form_name: str, data: object) -> FormDefinition | None:
    """Parse a form definition dict into a FormDefinition.

    Pure function — no filesystem access. Returns None if *data* is not a dict.
    """
    if not isinstance(data, dict):
        return None

    # Prefer explicit kind from YAML; fall back to name-based heuristic
    raw_kind = data.get("kind")
    if isinstance(raw_kind, str):
        kind = _KIND_MAP.get(raw_kind, KindType.QUANTITY)
    else:
        kind = kind_type_from_form_name(form_name)
        if kind is None:
            kind = KindType.QUANTITY

    unit_symbol = data.get("unit_symbol")
    if unit_symbol is not None and not isinstance(unit_symbol, str):
        unit_symbol = None
    # Treat explicit null as None
    if unit_symbol is None or unit_symbol == "":
        unit_symbol = None

    allowed = allowed_units_from_form_definition(data)

    parameters = data.get("parameters", {}) or {}

    # Read explicit dimensionless field; fall back to base == "ratio" heuristic
    _explicit = data.get("dimensionless")
    if isinstance(_explicit, bool):
        is_dimensionless = _explicit
    else:
        is_dimensionless = (
            data.get("base") == "ratio"
            or (unit_symbol is None and kind == KindType.QUANTITY
                and form_name not in ("structural",))
        )

    # Read dimensions field (dict of SI dimension symbol -> integer exponent)
    raw_dims = data.get("dimensions")
    dimensions: dict[str, int] | None = None
    if isinstance(raw_dims, dict):
        dimensions = {str(k): int(v) for k, v in raw_dims.items()}

    # Read extra_units and add their symbols to allowed_units
    extra_units: list[dict[str, Any]] = []
    raw_extra = data.get("extra_units")
    if isinstance(raw_extra, list):
        for entry in raw_extra:
            if isinstance(entry, dict) and isinstance(entry.get("symbol"), str):
                extra_units.append(entry)
                allowed.add(entry["symbol"])

    # Build UnitConversion objects from common_alternatives
    conversions: dict[str, UnitConversion] = {}
    for alt in data.get("common_alternatives", []) or []:
        if not isinstance(alt, dict):
            continue
        unit = alt.get("unit")
        if not isinstance(unit, str) or not unit:
            continue
        conv_type = alt.get("type", "multiplicative")
        conversions[unit] = UnitConversion(
            unit=unit,
            type=conv_type,
            multiplier=float(alt.get("multiplier", 1.0)),
            offset=float(alt.get("offset", 0.0)),
            base=float(alt.get("base", 10.0)),
            divisor=float(alt.get("divisor", 1.0)),
            reference=float(alt.get("reference", 1.0)),
        )

    return FormDefinition(
        name=form_name,
        kind=kind,
        unit_symbol=unit_symbol,
        allowed_units=allowed,
        is_dimensionless=is_dimensionless,
        parameters=parameters,
        dimensions=dimensions,
        extra_units=extra_units,
        conversions=conversions,
    )


def load_form(forms_dir: Path, form_name: str | None) -> FormDefinition | None:
    """Load a single form definition and return a FormDefinition, or None.

    Results are cached by (forms_dir, form_name) to avoid redundant disk reads.
    """
    if not isinstance(form_name, str) or not form_name:
        return None
    cache_key = (str(forms_dir), form_name)
    if cache_key in _form_cache:
        return _form_cache[cache_key]
    form_path = forms_dir / f"{form_name}.yaml"
    if not form_path.exists():
        _form_cache[cache_key] = None
        return None
    with open(form_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    result = parse_form(form_name, data)
    _form_cache[cache_key] = result
    return result


def normalize_to_si(value: float, unit: str | None, form: FormDefinition) -> float:
    """Convert a value from the given unit to the form's canonical (SI) unit."""
    if unit is None or unit == form.unit_symbol:
        return value
    if form.unit_symbol is None:
        raise ValueError(
            f"Cannot convert '{unit}' for dimensionless form '{form.name}'"
        )
    # Use explicit conversions for logarithmic (pint can't handle these)
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.reference * conv.base ** (value / conv.divisor)
    # Fall through to pint for multiplicative, affine, and auto-prefix units
    try:
        q = ureg.Quantity(value, _pint_unit(unit))
        return q.to(_pint_unit(form.unit_symbol)).magnitude
    except (pint.UndefinedUnitError, pint.DimensionalityError) as e:
        raise ValueError(
            f"Cannot convert '{unit}' to '{form.unit_symbol}' for form '{form.name}': {e}"
        )


def from_si(si_value: float, unit: str | None, form: FormDefinition) -> float:
    """Convert an SI value back to the given unit."""
    if unit is None or unit == form.unit_symbol:
        return si_value
    if form.unit_symbol is None:
        raise ValueError(
            f"Cannot convert to '{unit}' for dimensionless form '{form.name}'"
        )
    # Use explicit conversions for logarithmic (pint can't handle these)
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.divisor * math.log(si_value / conv.reference, conv.base)
    # Fall through to pint for multiplicative, affine, and auto-prefix units
    try:
        q = ureg.Quantity(si_value, _pint_unit(form.unit_symbol))
        return q.to(_pint_unit(unit)).magnitude
    except (pint.UndefinedUnitError, pint.DimensionalityError) as e:
        raise ValueError(
            f"Cannot convert '{form.unit_symbol}' to '{unit}' for form '{form.name}': {e}"
        )


def load_all_forms(forms_dir: Path) -> dict[str, FormDefinition]:
    """Load all form YAML files and return a registry keyed by form name."""
    registry: dict[str, FormDefinition] = {}
    if not forms_dir.exists():
        return registry
    for entry in sorted(forms_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".yaml":
            fd = load_form(forms_dir, entry.stem)
            if fd is not None:
                registry[fd.name] = fd
    return registry


def load_all_forms_from_reader(reader: object) -> dict[str, FormDefinition]:
    """Load all form definitions via a TreeReader.

    *reader* must implement ``list_yaml(subdir) -> list[(stem, bytes)]``.
    """
    registry: dict[str, FormDefinition] = {}
    for stem, raw_bytes in reader.list_yaml("forms"):  # type: ignore[attr-defined]
        data = yaml.safe_load(raw_bytes)
        fd = parse_form(stem, data) if isinstance(data, dict) else None
        if fd is not None:
            registry[fd.name] = fd
    return registry


# ── Pure form utilities ─────────────────────────────────────────────


def forms_with_dimensions(
    forms: Sequence[FormDefinition | None],
) -> list[FormDefinition] | None:
    """Filter a form list, returning None if any form lacks dimensions."""
    concrete: list[FormDefinition] = []
    for form_def in forms:
        if form_def is None or form_def.dimensions is None:
            return None
        concrete.append(form_def)
    return concrete


def required_dimensions(form_def: FormDefinition) -> dict[str, int]:
    """Return dimensions dict, raising ValueError if None."""
    dimensions = form_def.dimensions
    if dimensions is None:
        raise ValueError(f"form '{form_def.name}' has no dimensions")
    return dimensions


def verify_form_algebra_dimensions(
    output: FormDefinition,
    inputs: list[FormDefinition],
    operation: str,
) -> bool:
    """Check dimensional consistency of a form algebra expression.

    Returns True if the operation is dimensionally valid, False otherwise.
    Requires bridgman and sympy.
    """
    if output.dimensions is None:
        return False
    concrete_inputs = forms_with_dimensions(inputs)
    if concrete_inputs is None:
        return False
    try:
        import sympy as sp
        from bridgman import verify_expr

        dim_map: dict[str, dict[str, int]] = {}
        dim_map[output.name] = dict(required_dimensions(output))
        for inp_fd in concrete_inputs:
            dim_map[inp_fd.name] = dict(required_dimensions(inp_fd))

        form_parsed = sp.sympify(operation)
        if not isinstance(form_parsed, sp.Eq):
            return False
        return bool(verify_expr(form_parsed, dim_map))
    except (KeyError, ValueError, ImportError):
        return False


def dims_signature(dimensions: dict[str, int] | None) -> str | None:
    """Canonical string key for a dimension dict.

    Returns a sorted, zero-stripped representation like ``'L:1,M:1,T:-2'``,
    an empty string for dimensionless (all-zero or empty dict),
    or ``None`` when *dimensions* is ``None``.
    """
    if dimensions is None:
        return None
    cleaned = {k: v for k, v in dimensions.items() if v != 0}
    if not cleaned:
        return ""
    return ",".join(f"{k}:{v}" for k, v in sorted(cleaned.items()))


def json_safe(obj: Any) -> Any:
    """Recursively convert date objects to ISO strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj


def kind_type_from_form_name(form: str | None) -> KindType | None:
    """Map a concept form name to the CEL/type-checking kind."""
    if not isinstance(form, str) or not form:
        return None
    if form == "category":
        return KindType.CATEGORY
    if form == "structural":
        return KindType.STRUCTURAL
    if form == "boolean":
        return KindType.BOOLEAN
    return KindType.QUANTITY


def kind_value_from_form_name(form: str | None) -> str:
    """Map a concept form name to the sidecar kind_type string."""
    kind = kind_type_from_form_name(form)
    if kind is None:
        return "unknown"
    if kind == KindType.QUANTITY:
        return "quantity"
    return kind.value


def load_form_definition(forms_dir: Path, form_name: str | None) -> dict[str, Any]:
    """Load a form definition YAML file if present."""
    if not isinstance(form_name, str) or not form_name:
        return {}
    form_path = forms_dir / f"{form_name}.yaml"
    if not form_path.exists():
        return {}
    with open(form_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def allowed_units_from_form_definition(form_definition: dict[str, Any]) -> set[str]:
    """Extract allowed unit symbols from a form definition."""
    allowed: set[str] = set()

    unit_symbol = form_definition.get("unit_symbol")
    if isinstance(unit_symbol, str) and unit_symbol:
        allowed.add(unit_symbol)

    for alt in form_definition.get("common_alternatives", []) or []:
        if not isinstance(alt, dict):
            continue
        unit = alt.get("unit")
        if isinstance(unit, str) and unit:
            allowed.add(unit)

    return allowed


# ── Form file schema validation ──────────────────────────────────────

_form_schema_cache: dict | None = None


def _load_form_schema() -> dict:
    """Load the form JSON Schema, caching the result."""
    global _form_schema_cache
    if _form_schema_cache is None:
        schema = load_resource_json("schemas/form.schema.json")
        if not isinstance(schema, dict):
            raise TypeError("schemas/form.schema.json must decode to a JSON object")
        _form_schema_cache = schema
    assert _form_schema_cache is not None
    return _form_schema_cache


def validate_form_files(forms_dir: Path) -> list[str]:
    """Validate all form YAML files against the form JSON Schema.

    Returns a list of error strings (empty means all valid).
    """
    errors: list[str] = []
    if not forms_dir.exists():
        return errors

    schema = _load_form_schema()

    for entry in sorted(forms_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        with open(entry, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            errors.append(f"{entry.stem}: form file is not a YAML mapping")
            continue
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{entry.stem}: {e.message}")

        # Cross-check: dimensions vs dimensionless consistency
        dims = data.get("dimensions")
        is_dimless = data.get("dimensionless", False)
        has_unit = data.get("unit_symbol") is not None
        if isinstance(dims, dict) and len(dims) > 0 and is_dimless is True:
            errors.append(
                f"{entry.stem}: non-empty dimensions conflicts with "
                f"dimensionless=true")
        if isinstance(dims, dict) and len(dims) == 0 and is_dimless is False and has_unit:
            errors.append(
                f"{entry.stem}: empty dimensions conflicts with "
                f"dimensionless=false for a quantity with unit_symbol")

        # Cross-check: name field must match filename
        name = data.get("name")
        if name != entry.stem:
            errors.append(
                f"{entry.stem}: 'name' field ('{name}') does not match "
                f"filename '{entry.stem}'")

    return errors

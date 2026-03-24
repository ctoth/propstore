"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from propstore.cel_checker import KindType



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
    if not isinstance(data, dict):
        return None

    # Prefer explicit kind from YAML; fall back to name-based heuristic
    raw_kind = data.get("kind")
    if isinstance(raw_kind, str):
        _KIND_MAP = {
            "quantity": KindType.QUANTITY,
            "category": KindType.CATEGORY,
            "boolean": KindType.BOOLEAN,
            "structural": KindType.STRUCTURAL,
        }
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

    result = FormDefinition(
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
    _form_cache[cache_key] = result
    return result


def normalize_to_si(value: float, unit: str | None, form: FormDefinition) -> float:
    """Convert a value from the given unit to the form's canonical (SI) unit."""
    if unit is None or unit == form.unit_symbol:
        return value
    if unit not in form.conversions:
        raise ValueError(f"Unknown unit '{unit}' for form '{form.name}'")
    conv = form.conversions[unit]
    if conv.type == "multiplicative":
        return value * conv.multiplier
    elif conv.type == "affine":
        return value * conv.multiplier + conv.offset
    elif conv.type == "logarithmic":
        return conv.reference * conv.base ** (value / conv.divisor)
    raise ValueError(f"Unknown conversion type '{conv.type}'")


def from_si(si_value: float, unit: str | None, form: FormDefinition) -> float:
    """Convert an SI value back to the given unit."""
    if unit is None or unit == form.unit_symbol:
        return si_value
    if unit not in form.conversions:
        raise ValueError(f"Unknown unit '{unit}' for form '{form.name}'")
    conv = form.conversions[unit]
    if conv.type == "multiplicative":
        return si_value / conv.multiplier
    elif conv.type == "affine":
        return (si_value - conv.offset) / conv.multiplier
    elif conv.type == "logarithmic":
        return conv.divisor * math.log(si_value / conv.reference, conv.base)
    raise ValueError(f"Unknown conversion type '{conv.type}'")


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

_FORM_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "generated" / "form.schema.json"

_form_schema_cache: dict | None = None


def _load_form_schema() -> dict:
    """Load the form JSON Schema, caching the result."""
    global _form_schema_cache
    if _form_schema_cache is None:
        with open(_FORM_SCHEMA_PATH) as f:
            _form_schema_cache = json.load(f)
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

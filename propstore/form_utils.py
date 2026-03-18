"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from propstore.cel_checker import KindType


# ── Dimensionless unit markers ────────────────────────────────────────
DIMENSIONLESS_UNITS = frozenset({
    "ratio", "dimensionless", "%", "fraction", "",
})

LEVEL_UNITS = frozenset({
    "dB", "dB SPL", "dB HL", "dB SL",
})


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


_form_cache: dict[tuple[str, str], FormDefinition | None] = {}


def load_form(forms_dir: Path, form_name: object) -> FormDefinition | None:
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
    with open(form_path) as f:
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

    result = FormDefinition(
        name=form_name,
        kind=kind,
        unit_symbol=unit_symbol,
        allowed_units=allowed,
        is_dimensionless=is_dimensionless,
        parameters=parameters,
        dimensions=dimensions,
    )
    _form_cache[cache_key] = result
    return result


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


def json_safe(obj: Any) -> Any:
    """Recursively convert date objects to ISO strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj


def kind_type_from_form_name(form: object) -> KindType | None:
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


def kind_value_from_form_name(form: object) -> str:
    """Map a concept form name to the sidecar kind_type string."""
    kind = kind_type_from_form_name(form)
    if kind is None:
        return "unknown"
    if kind == KindType.QUANTITY:
        return "quantity"
    return kind.value


def load_form_definition(forms_dir: Path, form_name: object) -> dict[str, Any]:
    """Load a form definition YAML file if present."""
    if not isinstance(form_name, str) or not form_name:
        return {}
    form_path = forms_dir / f"{form_name}.yaml"
    if not form_path.exists():
        return {}
    with open(form_path) as f:
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
        with open(entry) as f:
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

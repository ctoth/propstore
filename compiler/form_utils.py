"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from compiler.cel_checker import KindType


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

    # Determine dimensionless: ratio forms, level, dimensionless_compound
    is_dimensionless = (
        data.get("base") == "ratio"
        or form_name in ("level", "dimensionless_compound")
        or (unit_symbol is None and kind == KindType.QUANTITY
            and form_name not in ("structural",))
    )

    result = FormDefinition(
        name=form_name,
        kind=kind,
        unit_symbol=unit_symbol,
        allowed_units=allowed,
        is_dimensionless=is_dimensionless,
        parameters=parameters,
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

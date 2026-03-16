"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import yaml

from compiler.cel_checker import KindType


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

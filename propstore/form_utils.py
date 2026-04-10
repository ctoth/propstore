"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Sequence
from typing import Any

import msgspec
import pint

from propstore.cel_checker import KindType
from propstore.document_schema import DocumentSchemaError, DocumentStruct, decode_document_path
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore.resources import load_resource_json

# Module-level unit registry for pint conversions
ureg = pint.UnitRegistry()

# Map propstore unit symbols to pint-recognized names
_PINT_ALIASES: dict[str, str] = {
    "°C": "degC",
    "°F": "degF",
    "µ": "u",
    "d": "day",
    "wk": "week",
    "mo": "month",
    "yr": "year",
}


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


@dataclass(frozen=True)
class ExtraUnitDefinition:
    """Additional unit metadata declared on a form."""

    symbol: str
    dimensions: dict[str, int]


@dataclass
class FormDefinition:
    """Structured representation of a loaded form YAML file."""
    name: str
    kind: KindType
    unit_symbol: str | None = None
    allowed_units: set[str] = field(default_factory=set)
    is_dimensionless: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)
    dimensions: dict[str, int] | None = None
    extra_units: tuple[ExtraUnitDefinition, ...] = ()
    conversions: dict[str, UnitConversion] = field(default_factory=dict)


class FormAlternativeDocument(DocumentStruct):
    unit: str
    type: str
    multiplier: float = 1.0
    offset: float = 0.0
    base: float = 10.0
    divisor: float = 1.0
    reference: float = 1.0


class FormExtraUnitDocument(DocumentStruct):
    symbol: str
    dimensions: dict[str, int] = msgspec.field(default_factory=dict)


class FormDocument(DocumentStruct):
    name: str
    dimensionless: bool
    base: str | None = None
    unit_symbol: str | None = None
    qudt: str | None = None
    parameters: dict[str, Any] = msgspec.field(default_factory=dict)
    common_alternatives: tuple[FormAlternativeDocument, ...] = ()
    kind: str | None = None
    note: str | None = None
    dimensions: dict[str, int] | None = None
    extra_units: tuple[FormExtraUnitDocument, ...] = ()


_form_cache: dict[tuple[str, str], FormDefinition | None] = {}
_form_schema_cache: dict[str, Any] | None = None


def clear_form_cache() -> None:
    """Clear the module-level form cache, forcing reload from disk on next access."""
    _form_cache.clear()


def _load_form_schema() -> dict[str, Any]:
    """Load the packaged form JSON schema, caching the result."""
    global _form_schema_cache
    if _form_schema_cache is None:
        schema = load_resource_json("schemas/form.schema.json")
        if not isinstance(schema, dict):
            raise TypeError("schemas/form.schema.json must decode to a JSON object")
        _form_schema_cache = schema
    return _form_schema_cache


def _path_cache_key(forms_dir: Path | KnowledgePath) -> str:
    if isinstance(forms_dir, Path):
        return str(forms_dir.resolve())
    return forms_dir.cache_key()


_KIND_MAP = {
    "quantity": KindType.QUANTITY,
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
    "timepoint": KindType.TIMEPOINT,
}


def parse_form(form_name: str, data: FormDocument) -> FormDefinition:
    """Parse a typed form document into a FormDefinition."""

    raw_kind = data.kind
    if isinstance(raw_kind, str):
        kind = _KIND_MAP.get(raw_kind, KindType.QUANTITY)
    else:
        kind = kind_type_from_form_name(form_name)
        if kind is None:
            kind = KindType.QUANTITY

    unit_symbol = data.unit_symbol
    # Treat explicit null as None
    if unit_symbol is None or unit_symbol == "":
        unit_symbol = None

    allowed = allowed_units_from_form_definition(data)

    parameters = dict(data.parameters)

    is_dimensionless = data.dimensionless

    dimensions = None if data.dimensions is None else dict(data.dimensions)

    extra_units = tuple(
        ExtraUnitDefinition(
            symbol=entry.symbol,
            dimensions=dict(entry.dimensions),
        )
        for entry in data.extra_units
    )
    for entry in extra_units:
        allowed.add(entry.symbol)

    conversions: dict[str, UnitConversion] = {}
    for alt in data.common_alternatives:
        conversions[alt.unit] = UnitConversion(
            unit=alt.unit,
            type=alt.type,
            multiplier=float(alt.multiplier),
            offset=float(alt.offset),
            base=float(alt.base),
            divisor=float(alt.divisor),
            reference=float(alt.reference),
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


def load_form(forms_dir: Path | KnowledgePath, form_name: str | None) -> FormDefinition | None:
    """Load a single form definition and return a FormDefinition, or None.

    Results are cached by (forms_dir, form_name) to avoid redundant reads.
    """
    if not isinstance(form_name, str) or not form_name:
        return None
    forms_root = coerce_knowledge_path(forms_dir)
    cache_key = (_path_cache_key(forms_dir), form_name)
    if cache_key in _form_cache:
        return _form_cache[cache_key]
    form_path = forms_root / f"{form_name}.yaml"
    if not form_path.exists():
        _form_cache[cache_key] = None
        return None
    document = load_form_definition(forms_root, form_name)
    if document is None:
        _form_cache[cache_key] = None
        return None
    result = parse_form(form_name, document)
    _form_cache[cache_key] = result
    return result


def load_form_path(forms_dir: KnowledgePath, form_name: str | None) -> FormDefinition | None:
    """Load a single form definition from a knowledge-tree path."""
    return load_form(forms_dir, form_name)


def normalize_to_si(value: float, unit: str | None, form: FormDefinition) -> float:
    """Convert a value from the given unit to the form's canonical (SI) unit."""
    if unit is None or unit == form.unit_symbol:
        return value
    if form.unit_symbol is None:
        raise ValueError(
            f"Cannot convert '{unit}' for dimensionless form '{form.name}'"
        )
    # Use explicit conversions when available (preferred over pint)
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.reference * conv.base ** (value / conv.divisor)
        if conv.type == "multiplicative":
            return value * conv.multiplier
        if conv.type == "affine":
            return value * conv.multiplier + conv.offset
    # Fall through to pint for auto-prefix units and anything not explicitly listed
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
    # Use explicit conversions when available (preferred over pint)
    if unit in form.conversions:
        conv = form.conversions[unit]
        if conv.type == "logarithmic":
            return conv.divisor * math.log(si_value / conv.reference, conv.base)
        if conv.type == "multiplicative":
            return si_value / conv.multiplier
        if conv.type == "affine":
            return (si_value - conv.offset) / conv.multiplier
    # Fall through to pint for auto-prefix units and anything not explicitly listed
    try:
        q = ureg.Quantity(si_value, _pint_unit(form.unit_symbol))
        return q.to(_pint_unit(unit)).magnitude
    except (pint.UndefinedUnitError, pint.DimensionalityError) as e:
        raise ValueError(
            f"Cannot convert '{form.unit_symbol}' to '{unit}' for form '{form.name}': {e}"
        )


def load_all_forms(forms_dir: Path | KnowledgePath) -> dict[str, FormDefinition]:
    """Load all form YAML files and return a registry keyed by form name."""
    registry: dict[str, FormDefinition] = {}
    forms_root = coerce_knowledge_path(forms_dir)
    if not forms_root.exists():
        return registry
    for entry in forms_root.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            fd = load_form(forms_root, entry.stem)
            if fd is not None:
                registry[fd.name] = fd
    return registry


def load_all_forms_path(forms_dir: KnowledgePath) -> dict[str, FormDefinition]:
    """Load all form YAML files from a knowledge-tree forms directory."""
    registry: dict[str, FormDefinition] = {}
    if not forms_dir.exists():
        return registry
    for entry in forms_dir.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            fd = load_form_path(forms_dir, entry.stem)
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
    if form == "timepoint":
        return KindType.TIMEPOINT
    return KindType.QUANTITY


def kind_value_from_form_name(form: str | None) -> str:
    """Map a concept form name to the sidecar kind_type string."""
    kind = kind_type_from_form_name(form)
    if kind is None:
        return "unknown"
    if kind == KindType.QUANTITY:
        return "quantity"
    return kind.value


def load_form_definition(
    forms_dir: Path | KnowledgePath,
    form_name: str | None,
) -> FormDocument | None:
    """Load a typed form document YAML file if present."""

    if not isinstance(form_name, str) or not form_name:
        return None
    form_path = coerce_knowledge_path(forms_dir) / f"{form_name}.yaml"
    if not form_path.exists():
        return None
    return decode_document_path(form_path, FormDocument)


def allowed_units_from_form_definition(form_definition: FormDocument) -> set[str]:
    """Extract allowed unit symbols from a typed form document."""

    allowed: set[str] = set()

    unit_symbol = form_definition.unit_symbol
    if unit_symbol:
        allowed.add(unit_symbol)

    for alt in form_definition.common_alternatives:
        if alt.unit:
            allowed.add(alt.unit)

    return allowed


def validate_form_files(forms_dir: Path | KnowledgePath) -> list[str]:
    """Validate all form YAML files against the typed document schema."""

    errors: list[str] = []
    forms_root = coerce_knowledge_path(forms_dir)
    if not forms_root.exists():
        return errors

    for entry in forms_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue

        try:
            document = decode_document_path(entry, FormDocument)
        except DocumentSchemaError as exc:
            errors.append(str(exc))
            continue

        dims = document.dimensions
        is_dimless = document.dimensionless
        has_unit = document.unit_symbol is not None
        if dims is not None and len(dims) > 0 and is_dimless:
            errors.append(
                f"{entry.stem}: non-empty dimensions conflicts with "
                f"dimensionless=true")
        if dims is not None and len(dims) == 0 and not is_dimless and has_unit:
            errors.append(
                f"{entry.stem}: empty dimensions conflicts with "
                f"dimensionless=false for a quantity with unit_symbol")

        if document.name != entry.stem:
            errors.append(
                f"{entry.stem}: 'name' field ('{document.name}') does not match "
                f"filename '{entry.stem}'")

    return errors

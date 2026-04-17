"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.artifacts.documents.forms import (
    FormDocument,
)
from propstore.cel_checker import KindType
from propstore.artifacts.schema import DocumentSchemaError, decode_document_path
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore import dimensions as dimension_api
from propstore.diagnostics import ValidationResult
from propstore.resources import load_resource_json

if TYPE_CHECKING:
    from propstore.repository import Repository


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
    extra_units: tuple[dimension_api.ExtraUnitDefinition, ...] = ()
    conversions: dict[str, dimension_api.UnitConversion] = field(default_factory=dict)


class FormNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Form '{name}' not found")
        self.name = name


@dataclass(frozen=True)
class FormAlgebraDecomposition:
    input_forms: tuple[str, ...]
    source_formula: object
    source_concept_id: object


@dataclass(frozen=True)
class FormAlgebraUse:
    output_form: object
    input_forms: tuple[str, ...]


@dataclass(frozen=True)
class FormShowReport:
    yaml_text: str
    form: FormDefinition | None
    decompositions: tuple[FormAlgebraDecomposition, ...] = ()
    uses: tuple[FormAlgebraUse, ...] = ()


_form_cache: dict[tuple[str, str], FormDefinition | None] = {}
_form_schema_cache: dict[str, Any] | None = None


def show_form(
    repo: Repository,
    name: str,
) -> FormShowReport:
    forms_tree = repo.tree() / "forms"
    path = forms_tree / f"{name}.yaml"
    if not path.exists():
        raise FormNotFoundError(name)

    form_def = load_form_path(forms_tree, name)
    decompositions: tuple[FormAlgebraDecomposition, ...] = ()
    uses: tuple[FormAlgebraUse, ...] = ()
    if repo.sidecar_path.exists():
        try:
            from propstore.world import WorldModel

            with WorldModel(repo) as world:
                decompositions = tuple(
                    FormAlgebraDecomposition(
                        input_forms=tuple(json.loads(entry["input_forms"])),
                        source_formula=entry.get("source_formula"),
                        source_concept_id=entry.get("source_concept_id", "?"),
                    )
                    for entry in world.form_algebra_for(name)
                )
                uses = tuple(
                    FormAlgebraUse(
                        output_form=entry["output_form"],
                        input_forms=tuple(json.loads(entry["input_forms"])),
                    )
                    for entry in world.form_algebra_using(name)
                )
        except Exception:
            decompositions = ()
            uses = ()

    return FormShowReport(
        yaml_text=path.read_text(),
        form=form_def,
        decompositions=decompositions,
        uses=uses,
    )


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
        dimension_api.ExtraUnitDefinition(
            symbol=entry.symbol,
            dimensions=dict(entry.dimensions),
        )
        for entry in data.extra_units
    )
    for entry in extra_units:
        allowed.add(entry.symbol)

    conversions: dict[str, dimension_api.UnitConversion] = {}
    for alt in data.common_alternatives:
        conversions[alt.unit] = dimension_api.UnitConversion(
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


def validate_form_files(forms_dir: Path | KnowledgePath) -> ValidationResult:
    """Validate all form YAML files against the typed document schema."""

    result = ValidationResult()
    forms_root = coerce_knowledge_path(forms_dir)
    if not forms_root.exists():
        return result

    for entry in forms_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue

        try:
            document = decode_document_path(entry, FormDocument)
        except DocumentSchemaError as exc:
            result.errors.append(str(exc))
            continue

        dims = document.dimensions
        is_dimless = document.dimensionless
        has_unit = document.unit_symbol is not None
        if dims is not None and len(dims) > 0 and is_dimless:
            result.errors.append(
                f"{entry.stem}: non-empty dimensions conflicts with "
                f"dimensionless=true")
        if dims is not None and len(dims) == 0 and not is_dimless and has_unit:
            result.errors.append(
                f"{entry.stem}: empty dimensions conflicts with "
                f"dimensionless=false for a quantity with unit_symbol")

        if document.name != entry.stem:
            result.errors.append(
                f"{entry.stem}: 'name' field ('{document.name}') does not match "
                f"filename '{entry.stem}'")

    return result

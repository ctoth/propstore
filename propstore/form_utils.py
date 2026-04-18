"""Shared helpers for form metadata, kind mapping, and JSON-safe serialization."""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from propstore.artifacts.documents.forms import (
    FormDocument,
)
from propstore.artifacts.families import FORM_FAMILY
from propstore.artifacts.refs import FormRef
from propstore.cel_checker import KindType
from propstore.artifacts.schema import DocumentSchemaError, convert_document_value, decode_document_path
from propstore.core.concepts import load_concepts
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path
from propstore import dimensions as dimension_api
from propstore.diagnostics import ValidationResult

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


class FormWorkflowError(Exception):
    """Raised when a form authoring workflow cannot complete."""


class FormReferencedError(FormWorkflowError):
    def __init__(self, name: str, references: tuple[str, ...]) -> None:
        super().__init__(f"Form '{name}' is referenced by {len(references)} concept(s)")
        self.references = references


@dataclass(frozen=True)
class FormListItem:
    name: str
    unit_symbol: str | None
    dimensions: dict[str, int] | None
    is_dimensionless: bool


@dataclass(frozen=True)
class FormAddRequest:
    name: str
    unit_symbol: str | None = None
    qudt: str | None = None
    base: str | None = None
    dimensions_json: str | None = None
    dimensionless: str | None = None
    common_alternatives_json: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class FormAddReport:
    path: Path
    document: FormDocument
    created: bool


@dataclass(frozen=True)
class FormRemoveReport:
    path: Path
    removed: bool
    references: tuple[str, ...]


@dataclass(frozen=True)
class FormValidationReport:
    count: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


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


def parse_dims_spec(spec: str) -> dict[str, int]:
    """Parse a CLI dimension filter like ``M:1,L:1,T:-2``."""
    result: dict[str, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        result[key.strip()] = int(val.strip())
    return result


def format_dims_col(dimensions: dict[str, int] | None, is_dimensionless: bool) -> str:
    """Format dimensions for the form list display column."""
    if dimensions is None:
        return "(dimensionless)" if is_dimensionless else ""
    if not dimensions or all(v == 0 for v in dimensions.values()):
        return "(dimensionless)"
    try:
        from bridgman import format_dims

        return format_dims(dimensions)
    except ImportError:
        return str(dimensions)


def list_form_items(
    repo: Repository,
    *,
    dims_filter: str | None,
) -> tuple[FormListItem, ...] | None:
    forms_tree = repo.tree() / "forms"
    if not forms_tree.exists():
        return None

    registry = load_all_forms_path(forms_tree)
    filter_dims = parse_dims_spec(dims_filter) if dims_filter is not None else None
    items: list[FormListItem] = []
    for form in sorted(registry.values(), key=lambda item: item.name):
        if filter_dims is not None:
            from bridgman import dims_equal

            form_dims = form.dimensions or ({} if form.is_dimensionless else None)
            if form_dims is None or not dims_equal(form_dims, filter_dims):
                continue
        items.append(
            FormListItem(
                name=form.name,
                unit_symbol=form.unit_symbol,
                dimensions=form.dimensions,
                is_dimensionless=form.is_dimensionless,
            )
        )
    return tuple(items)


def _parse_json_option(raw: str, *, option_name: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FormWorkflowError(f"Invalid JSON for {option_name}: {raw}") from exc


def _form_add_payload(request: FormAddRequest) -> dict[str, object]:
    dims_parsed: object | None = None
    if request.dimensions_json is not None:
        dims_parsed = _parse_json_option(
            request.dimensions_json,
            option_name="--dimensions",
        )
        if not isinstance(dims_parsed, dict):
            raise FormWorkflowError("--dimensions must decode to a JSON object")

    if request.dimensionless is not None:
        is_dimless = request.dimensionless.lower() in ("true", "1", "yes")
    elif isinstance(dims_parsed, dict) and len(dims_parsed) > 0:
        is_dimless = False
    else:
        is_dimless = isinstance(dims_parsed, dict) and len(dims_parsed) == 0

    data: dict[str, object] = {
        "name": request.name,
        "dimensionless": is_dimless,
    }
    if request.base is not None:
        data["base"] = request.base
    if request.unit_symbol is not None:
        data["unit_symbol"] = request.unit_symbol
    if request.qudt is not None:
        data["qudt"] = request.qudt
    if dims_parsed is not None:
        data["dimensions"] = dims_parsed
    if request.common_alternatives_json is not None:
        data["common_alternatives"] = _parse_json_option(
            request.common_alternatives_json,
            option_name="--common-alternatives",
        )
    if request.note is not None:
        data["note"] = request.note
    return data


def add_form(repo: Repository, request: FormAddRequest, *, dry_run: bool) -> FormAddReport:
    ref = FormRef(request.name)
    relpath = FORM_FAMILY.resolve_ref(repo, ref).relpath
    path = repo.root / relpath
    if (repo.tree() / relpath).exists():
        raise FormWorkflowError(f"Form '{request.name}' already exists")

    source = (
        f"dry-run:{relpath}"
        if dry_run
        else relpath
    )
    document = convert_document_value(
        _form_add_payload(request),
        FormDocument,
        source=source,
    )
    if dry_run:
        return FormAddReport(path=path, document=document, created=False)

    repo.artifacts.save(
        FORM_FAMILY,
        ref,
        document,
        message=f"Add form: {request.name}",
    )
    repo.snapshot.sync_worktree()
    return FormAddReport(path=path, document=document, created=True)


def form_references(repo: Repository, name: str) -> tuple[str, ...]:
    references: list[str] = []
    for concept in load_concepts(repo.tree() / "concepts"):
        if concept.record.form == name:
            references.append(f"{concept.record.artifact_id} ({concept.filename})")
    return tuple(references)


def remove_form(
    repo: Repository,
    name: str,
    *,
    force: bool,
    dry_run: bool,
) -> FormRemoveReport:
    ref = FormRef(name)
    relpath = FORM_FAMILY.resolve_ref(repo, ref).relpath
    path = repo.root / relpath
    if not (repo.tree() / relpath).exists():
        raise FormNotFoundError(name)

    references = form_references(repo, name)
    if references and not force:
        raise FormReferencedError(name, references)
    if dry_run:
        return FormRemoveReport(path=path, removed=False, references=references)

    repo.artifacts.delete(
        cast(Any, FORM_FAMILY),
        ref,
        message=f"Remove form: {name}",
    )
    repo.snapshot.sync_worktree()
    return FormRemoveReport(path=path, removed=True, references=references)


def validate_forms(repo: Repository, name: str | None = None) -> FormValidationReport | None:
    forms_tree = repo.tree() / "forms"
    if not forms_tree.exists():
        return None

    if name is not None and not (forms_tree / f"{name}.yaml").exists():
        raise FormNotFoundError(name)

    form_result = validate_form_files(forms_tree)
    all_forms = {
        p.stem
        for p in forms_tree.iterdir()
        if p.is_file() and p.suffix == ".yaml"
    }
    concepts_tree = repo.tree() / "concepts"
    if concepts_tree.exists():
        for concept in load_concepts(concepts_tree):
            ref = concept.record.form
            if ref and ref not in all_forms:
                form_result.errors.append(
                    f"concept {concept.filename}: references missing form '{ref}'"
                )

    count = len([
        p for p in forms_tree.iterdir()
        if p.is_file() and p.suffix == ".yaml"
    ])
    return FormValidationReport(count=count, errors=tuple(form_result.errors))


def clear_form_cache() -> None:
    """Clear the module-level form cache, forcing reload from disk on next access."""
    _form_cache.clear()


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
        if dims is not None:
            for dimension_key in dims:
                if not dimension_key.isidentifier():
                    result.errors.append(
                        f"{entry.stem}: dimension key '{dimension_key}' must be an identifier"
                    )
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

"""Application-layer form workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.families.concepts.stages import parse_concept_record_document
from propstore.families.forms.documents import FormDocument
from propstore.families.forms.passes import run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, FormDefinition, LoadedForm
from propstore.families.registry import FormRef
from propstore.form_utils import parse_form
from quire.documents import convert_document_value

if TYPE_CHECKING:
    from propstore.repository import Repository


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
    qudt: str | None
    base: str | None
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


def show_form(
    repo: Repository,
    name: str,
) -> FormShowReport:
    ref = FormRef(name)
    document = repo.families.forms.load(ref)
    if document is None:
        raise FormNotFoundError(name)

    form_def = parse_form(document.name, document)
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
        yaml_text=repo.families.forms.render(document),
        form=form_def,
        decompositions=decompositions,
        uses=uses,
    )


def parse_dims_spec(spec: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        result[key.strip()] = int(val.strip())
    return result


def format_dims_col(dimensions: dict[str, int] | None, is_dimensionless: bool) -> str:
    if dimensions is None:
        return "(dimensionless)" if is_dimensionless else ""
    if not dimensions or all(value == 0 for value in dimensions.values()):
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
    refs = list(repo.families.forms.iter())
    if not refs:
        return None

    filter_dims = parse_dims_spec(dims_filter) if dims_filter is not None else None
    items: list[FormListItem] = []
    forms: list[tuple[FormDocument, FormDefinition]] = []
    for ref in refs:
        document = repo.families.forms.require(ref)
        forms.append((document, parse_form(document.name, document)))
    for document, form in sorted(forms, key=lambda item: item[1].name):
        if filter_dims is not None:
            from bridgman import dims_equal

            form_dims = form.dimensions or ({} if form.is_dimensionless else None)
            if form_dims is None or not dims_equal(form_dims, filter_dims):
                continue
        items.append(
            FormListItem(
                name=form.name,
                unit_symbol=form.unit_symbol,
                qudt=document.qudt,
                base=document.base,
                dimensions=form.dimensions,
                is_dimensionless=form.is_dimensionless,
            )
        )
    return tuple(items)


def search_form_items(
    repo: Repository,
    query: str,
    *,
    limit: int,
) -> tuple[FormListItem, ...] | None:
    items = list_form_items(repo, dims_filter=None)
    if items is None:
        return None
    needle = query.casefold()
    matches: list[FormListItem] = []
    for item in items:
        fields = (
            item.name,
            "" if item.unit_symbol is None else item.unit_symbol,
            "" if item.qudt is None else item.qudt,
            "" if item.base is None else item.base,
        )
        if needle and not any(needle in field.casefold() for field in fields):
            continue
        matches.append(item)
        if len(matches) >= limit:
            break
    return tuple(matches)


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
    relpath = repo.families.forms.address(ref).require_path()
    path = repo.root / relpath
    if repo.families.forms.load(ref) is not None:
        raise FormWorkflowError(f"Form '{request.name}' already exists")

    source = f"dry-run:{relpath}" if dry_run else relpath
    document = convert_document_value(
        _form_add_payload(request),
        FormDocument,
        source=source,
    )
    if dry_run:
        return FormAddReport(path=path, document=document, created=False)

    repo.families.forms.save(
        ref,
        document,
        message=f"Add form: {request.name}",
    )
    repo.snapshot.sync_worktree()
    return FormAddReport(path=path, document=document, created=True)


def form_references(repo: Repository, name: str) -> tuple[str, ...]:
    references: list[str] = []
    for ref in repo.families.concepts.iter():
        document = repo.families.concepts.require(ref)
        record = parse_concept_record_document(document)
        if record.form == name:
            references.append(f"{record.artifact_id} ({ref.name})")
    return tuple(references)


def remove_form(
    repo: Repository,
    name: str,
    *,
    force: bool,
    dry_run: bool,
) -> FormRemoveReport:
    ref = FormRef(name)
    relpath = repo.families.forms.address(ref).require_path()
    path = repo.root / relpath
    if repo.families.forms.load(ref) is None:
        raise FormNotFoundError(name)

    references = form_references(repo, name)
    if references and not force:
        raise FormReferencedError(name, references)
    if dry_run:
        return FormRemoveReport(path=path, removed=False, references=references)

    repo.families.forms.delete(
        ref,
        message=f"Remove form: {name}",
    )
    repo.snapshot.sync_worktree()
    return FormRemoveReport(path=path, removed=True, references=references)


def validate_forms(repo: Repository, name: str | None = None) -> FormValidationReport | None:
    refs = list(repo.families.forms.iter())
    if not refs:
        return None

    if name is not None and repo.families.forms.load(FormRef(name)) is None:
        raise FormNotFoundError(name)

    form_result = run_form_pipeline(
        [LoadedForm(filename=ref.name, document=repo.families.forms.require(ref)) for ref in refs]
    )
    errors = [error.render() for error in form_result.errors]
    form_registry = (
        form_result.output.registry
        if isinstance(form_result.output, FormCheckedRegistry)
        else {}
    )
    all_forms = {ref.name for ref in refs}

    for ref in repo.families.concepts.iter():
        record = parse_concept_record_document(repo.families.concepts.require(ref))
        form_ref = record.form
        if form_ref and form_ref not in form_registry and form_ref not in all_forms:
            errors.append(f"concept {ref.name}: references missing form '{form_ref}'")

    return FormValidationReport(count=len(refs), errors=tuple(errors))

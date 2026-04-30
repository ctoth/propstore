"""Form semantic stage objects and parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from propstore import dimensions as dimension_api
from propstore.cel_checker import KindType
from propstore.families.forms.documents import FormDocument
from quire.documents import decode_document_path
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path as coerce_knowledge_path


class FormStage(StrEnum):
    AUTHORED = "form.authored"
    NORMALIZED = "form.normalized"
    CHECKED = "form.checked"


@dataclass(frozen=True)
class LoadedForm:
    filename: str
    document: FormDocument


@dataclass
class FormDefinition:
    name: str
    kind: KindType
    unit_symbol: str | None = None
    allowed_units: set[str] = field(default_factory=set)
    is_dimensionless: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)
    dimensions: dict[str, int] | None = None
    extra_units: tuple[dimension_api.ExtraUnitDefinition, ...] = ()
    conversions: dict[str, dimension_api.UnitConversion] = field(default_factory=dict)
    delta_conversions: dict[str, dimension_api.UnitConversion] = field(default_factory=dict)


@dataclass(frozen=True)
class FormAuthoredSet:
    forms: tuple[LoadedForm, ...]


@dataclass(frozen=True)
class FormNormalizedRegistry:
    forms: tuple[LoadedForm, ...]
    registry: dict[str, FormDefinition]


@dataclass(frozen=True)
class FormCheckedRegistry:
    forms: tuple[LoadedForm, ...]
    registry: dict[str, FormDefinition]


_form_cache: dict[tuple[str, str], FormDefinition | None] = {}


_KIND_MAP = {
    "quantity": KindType.QUANTITY,
    "category": KindType.CATEGORY,
    "boolean": KindType.BOOLEAN,
    "structural": KindType.STRUCTURAL,
    "timepoint": KindType.TIMEPOINT,
}


def clear_form_cache() -> None:
    _form_cache.clear()


def _path_cache_key(forms_dir: Path | KnowledgePath) -> str:
    if isinstance(forms_dir, Path):
        return str(forms_dir.resolve())
    return forms_dir.cache_key()


def parse_form(form_name: str, data: FormDocument) -> FormDefinition:
    raw_kind = data.kind
    if isinstance(raw_kind, str):
        kind = _KIND_MAP.get(raw_kind, KindType.QUANTITY)
    else:
        kind = kind_type_from_form_name(form_name) or KindType.QUANTITY

    unit_symbol = data.unit_symbol
    if unit_symbol is None or unit_symbol == "":
        unit_symbol = None

    allowed = allowed_units_from_form_definition(data)
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
    delta_conversions: dict[str, dimension_api.UnitConversion] = {}
    for alt in data.delta_alternatives:
        delta_conversions[alt.unit] = dimension_api.UnitConversion(
            unit=alt.unit,
            type=alt.type,
            multiplier=float(alt.multiplier),
            offset=float(alt.offset),
            base=float(alt.base),
            divisor=float(alt.divisor),
            reference=float(alt.reference),
        )
        allowed.add(alt.unit)

    return FormDefinition(
        name=form_name,
        kind=kind,
        unit_symbol=unit_symbol,
        allowed_units=allowed,
        is_dimensionless=data.dimensionless,
        parameters=dict(data.parameters),
        dimensions=None if data.dimensions is None else dict(data.dimensions),
        extra_units=extra_units,
        conversions=conversions,
        delta_conversions=delta_conversions,
    )


def load_form(forms_dir: Path | KnowledgePath, form_name: str | None) -> FormDefinition | None:
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
    return load_form(forms_dir, form_name)


def load_all_forms(forms_dir: Path | KnowledgePath) -> dict[str, FormDefinition]:
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
    registry: dict[str, FormDefinition] = {}
    if not forms_dir.exists():
        return registry
    for entry in forms_dir.iterdir():
        if entry.is_file() and entry.suffix == ".yaml":
            fd = load_form_path(forms_dir, entry.stem)
            if fd is not None:
                registry[fd.name] = fd
    return registry


def kind_type_from_form_name(form: str | None) -> KindType | None:
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
    if not isinstance(form_name, str) or not form_name:
        return None
    form_path = coerce_knowledge_path(forms_dir) / f"{form_name}.yaml"
    if not form_path.exists():
        return None
    return decode_document_path(form_path, FormDocument)


def allowed_units_from_form_definition(form_definition: FormDocument) -> set[str]:
    allowed: set[str] = set()
    unit_symbol = form_definition.unit_symbol
    if unit_symbol:
        allowed.add(unit_symbol)
    for alt in form_definition.common_alternatives:
        if alt.unit:
            allowed.add(alt.unit)
    return allowed

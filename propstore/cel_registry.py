"""Typed CEL registry projection helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from propstore.cel_checker import ConceptInfo, KindType
from propstore.core.concepts import ConceptRecord
from propstore.core.row_types import ConceptRow
from propstore.form_utils import kind_type_from_form_name


def _category_metadata(form_parameters: Mapping[str, Any]) -> tuple[list[str], bool]:
    raw_values = form_parameters.get("values")
    values = [
        value
        for value in (
            raw_values
            if isinstance(raw_values, Sequence) and not isinstance(raw_values, str)
            else ()
        )
        if isinstance(value, str)
    ]
    raw_extensible = form_parameters.get("extensible")
    extensible = True if raw_extensible is None else bool(raw_extensible)
    return values, extensible


def _kind_type_from_optional_fields(
    *,
    kind_type: str | KindType | None,
    form: str | None,
) -> KindType:
    if isinstance(kind_type, KindType):
        return kind_type
    if isinstance(kind_type, str) and kind_type:
        try:
            return KindType(kind_type)
        except ValueError:
            pass
    inferred = None if not isinstance(form, str) or not form else kind_type_from_form_name(form)
    if inferred is None:
        raise ValueError("concept must define a valid kind_type or form")
    return inferred


def concept_info_from_concept_record(record: ConceptRecord) -> ConceptInfo:
    concept_id = str(record.artifact_id)
    if not concept_id:
        raise ValueError("concept record must define a non-empty artifact_id")
    if not isinstance(record.canonical_name, str) or not record.canonical_name:
        raise ValueError("concept record must define a non-empty canonical_name")
    kind = _kind_type_from_optional_fields(kind_type=None, form=record.form)
    if record.form_parameters is None:
        form_parameters: Mapping[str, Any] = {}
    elif isinstance(record.form_parameters, Mapping):
        form_parameters = record.form_parameters
    else:
        raise ValueError("concept record form_parameters must be a mapping")
    category_values, category_extensible = _category_metadata(form_parameters)
    return ConceptInfo(
        id=concept_id,
        canonical_name=record.canonical_name,
        kind=kind,
        category_values=category_values,
        category_extensible=category_extensible,
    )


def concept_info_from_concept_row(row: ConceptRow) -> ConceptInfo:
    concept_id = str(row.concept_id)
    if not concept_id:
        raise ValueError("concept row must define a non-empty concept_id")
    if not isinstance(row.canonical_name, str) or not row.canonical_name:
        raise ValueError("concept row must define a non-empty canonical_name")
    kind = _kind_type_from_optional_fields(kind_type=row.kind_type, form=row.form)
    form_parameters = _parse_row_form_parameters(row.form_parameters)
    category_values, category_extensible = _category_metadata(form_parameters)
    return ConceptInfo(
        id=concept_id,
        canonical_name=row.canonical_name,
        kind=kind,
        category_values=category_values,
        category_extensible=category_extensible,
    )


def _parse_row_form_parameters(value: str | None) -> Mapping[str, Any]:
    if value is None or value == "":
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"concept row has invalid form_parameters JSON: {exc}") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("concept row form_parameters must decode to a mapping")
    return parsed


def _build_registry(
    infos: Iterable[ConceptInfo],
) -> dict[str, ConceptInfo]:
    registry: dict[str, ConceptInfo] = {}
    ids_by_name: dict[str, str] = {}
    names_by_id: dict[str, str] = {}
    for info in infos:
        existing_id = ids_by_name.get(info.canonical_name)
        if existing_id is not None:
            raise ValueError(
                f"duplicate canonical_name '{info.canonical_name}' in CEL registry"
            )
        existing_name = names_by_id.get(info.id)
        if existing_name is not None:
            raise ValueError(f"duplicate concept id '{info.id}' in CEL registry")
        ids_by_name[info.canonical_name] = info.id
        names_by_id[info.id] = info.canonical_name
        registry[info.canonical_name] = info
    return registry


def build_canonical_cel_registry(
    records: Iterable[ConceptRecord],
) -> dict[str, ConceptInfo]:
    typed_records: list[ConceptRecord] = []
    for record in records:
        if not isinstance(record, ConceptRecord):
            raise TypeError(
                "build_canonical_cel_registry expects Iterable[ConceptRecord]"
            )
        typed_records.append(record)
    return _build_registry(
        concept_info_from_concept_record(record)
        for record in typed_records
    )


def build_store_cel_registry(
    rows: Iterable[ConceptRow],
) -> dict[str, ConceptInfo]:
    typed_rows: list[ConceptRow] = []
    for row in rows:
        if not isinstance(row, ConceptRow):
            raise TypeError("build_store_cel_registry expects Iterable[ConceptRow]")
        typed_rows.append(row)
    return _build_registry(
        concept_info_from_concept_row(row)
        for row in typed_rows
    )

"""Typed CEL registry projection helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.stages import kind_type_from_form_name


def _is_concept_row(row: object) -> bool:
    return all(
        hasattr(row, attr)
        for attr in (
            "concept_id",
            "canonical_name",
            "kind_type",
            "form",
            "form_parameters",
        )
    )


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
    inferred = (
        None
        if not isinstance(form, str) or not form
        else kind_type_from_form_name(form)
    )
    if inferred is None:
        raise ValueError("concept must define a valid kind_type or form")
    return inferred


def concept_info_from_concept_document(document: ConceptDocument) -> ConceptInfo:
    if document.artifact_id is None or not document.artifact_id:
        raise ValueError("concept document must define a non-empty artifact_id")
    concept_id = str(document.artifact_id)
    canonical_name = document.lexical_entry.canonical_form.written_rep
    if not canonical_name:
        raise ValueError("concept document must define a non-empty canonical_name")
    kind = _kind_type_from_optional_fields(
        kind_type=None,
        form=document.lexical_entry.physical_dimension_form,
    )
    form_parameters = document.form_parameters
    category_values = (
        list(form_parameters.values)
        if form_parameters is not None and form_parameters.values is not None
        else []
    )
    category_extensible = (
        True
        if form_parameters is None or form_parameters.extensible is None
        else form_parameters.extensible
    )
    return ConceptInfo(
        id=concept_id,
        canonical_name=canonical_name,
        kind=kind,
        category_values=category_values,
        category_extensible=category_extensible,
    )


def concept_info_from_concept_row(row: Any) -> ConceptInfo:
    concept_id = str(row.concept_id)
    if not concept_id:
        raise ValueError("concept row must define a non-empty concept_id")
    if not isinstance(row.canonical_name, str) or not row.canonical_name:
        raise ValueError("concept row must define a non-empty canonical_name")
    kind_type = row.kind_type
    form = row.form
    form_parameters_payload = row.form_parameters
    kind = _kind_type_from_optional_fields(
        kind_type=kind_type
        if isinstance(kind_type, str | KindType) or kind_type is None
        else None,
        form=form if isinstance(form, str) or form is None else None,
    )
    form_parameters = _parse_row_form_parameters(
        form_parameters_payload
        if isinstance(form_parameters_payload, str) or form_parameters_payload is None
        else None
    )
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
        raise ValueError(
            f"concept row has invalid form_parameters JSON: {exc}"
        ) from exc
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
    documents: Iterable[ConceptDocument],
) -> dict[str, ConceptInfo]:
    typed_documents: list[ConceptDocument] = []
    for document in documents:
        if not isinstance(document, ConceptDocument):
            raise TypeError(
                "build_canonical_cel_registry expects Iterable[ConceptDocument]"
            )
        typed_documents.append(document)
    return _build_registry(
        concept_info_from_concept_document(document) for document in typed_documents
    )


def build_store_cel_registry(
    rows: Iterable[Any],
) -> dict[str, ConceptInfo]:
    typed_rows: list[Any] = []
    for row in rows:
        if not _is_concept_row(row):
            raise TypeError("build_store_cel_registry expects Iterable[ConceptRow]")
        typed_rows.append(row)
    return _build_registry(concept_info_from_concept_row(row) for row in typed_rows)

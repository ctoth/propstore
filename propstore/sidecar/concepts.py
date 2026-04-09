"""Concept and form compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3

from ast_equiv import canonical_dump

from propstore.form_utils import (
    FormDefinition,
    kind_value_from_form_name,
    verify_form_algebra_dimensions,
)
from propstore.loaded import LoadedEntry
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols
from propstore.sidecar.concept_utils import (
    concept_artifact_id,
    concept_content_hash,
    concept_logical_ids,
    concept_primary_logical_id,
    concept_version_id,
    resolve_concept_reference,
)


def _concept_symbol_candidates(data: dict) -> tuple[str, ...]:
    seen: set[str] = set()
    candidates: list[str] = []

    def add(candidate: object) -> None:
        if not isinstance(candidate, str) or not candidate or candidate in seen:
            return
        seen.add(candidate)
        candidates.append(candidate)

    add(data.get("id"))
    add(data.get("canonical_name"))
    for logical_id in data.get("logical_ids", []) or []:
        if not isinstance(logical_id, dict):
            continue
        add(logical_id.get("value"))
        namespace = logical_id.get("namespace")
        value = logical_id.get("value")
        if isinstance(namespace, str) and isinstance(value, str) and namespace and value:
            add(f"{namespace}:{value}")
    for alias in data.get("aliases", []) or []:
        if not isinstance(alias, dict):
            continue
        add(alias.get("name"))
    return tuple(candidates)


def populate_form_algebra(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    form_registry: dict[str, FormDefinition],
) -> None:
    """Derive form algebra from concept parameterizations and populate the table."""
    if not form_registry:
        return

    id_to_form: dict[str, str] = {}
    id_to_symbols: dict[str, tuple[str, ...]] = {}
    for concept in concepts:
        concept_id = concept_artifact_id(concept.data)
        form_name = concept.data.get("form")
        if concept_id and form_name:
            id_to_form[concept_id] = form_name
            id_to_symbols[concept_id] = _concept_symbol_candidates(concept.data)

    seen: set[tuple] = set()

    for concept in concepts:
        concept_id = concept_artifact_id(concept.data)
        if not concept_id:
            continue
        output_form = id_to_form.get(concept_id)
        if not output_form:
            continue

        for parameterization in concept.data.get("parameterization_relationships", []) or []:
            inputs = parameterization.get("inputs", []) or []
            if not inputs:
                continue

            input_forms = []
            all_resolved = True
            for input_id in inputs:
                input_form = id_to_form.get(input_id)
                if not input_form:
                    all_resolved = False
                    break
                input_forms.append(input_form)
            if not all_resolved:
                continue

            sympy_str = parameterization.get("sympy")
            operation = ""
            if sympy_str:
                try:
                    operation = rewrite_parameterization_symbols(
                        sympy_str,
                        symbol_aliases={
                            concept_id: id_to_symbols.get(concept_id, ()),
                            **{
                                input_id: id_to_symbols.get(input_id, ())
                                for input_id in inputs
                            },
                        },
                        symbol_targets={
                            concept_id: output_form,
                            **{
                                input_id: id_to_form[input_id]
                                for input_id in inputs
                            },
                        },
                    )
                except Exception:
                    operation = sympy_str
            if not operation:
                operation = parameterization.get("formula", "")

            dim_verified = 1
            if sympy_str and operation:
                output_fd = form_registry.get(output_form)
                input_fd_list = [form_registry.get(form) for form in input_forms]
                if output_fd is not None and all(fd is not None for fd in input_fd_list):
                    if not verify_form_algebra_dimensions(
                        output_fd,
                        input_fd_list,  # type: ignore[arg-type]
                        operation,
                    ):
                        dim_verified = 0
                else:
                    dim_verified = 0

            try:
                canonical_operation = canonical_dump(operation, {})
            except Exception:
                canonical_operation = operation
            dedup_key = (output_form, tuple(sorted(input_forms)), canonical_operation)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            conn.execute(
                "INSERT INTO form_algebra "
                "(output_form, input_forms, operation, source_concept_id, "
                "source_formula, dim_verified) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    output_form,
                    json.dumps(input_forms),
                    operation,
                    concept_id,
                    parameterization.get("formula", ""),
                    dim_verified,
                ),
            )


def populate_forms(
    conn: sqlite3.Connection,
    form_registry: dict[str, FormDefinition],
) -> None:
    """Populate the form table from a pre-loaded form registry."""
    for form_definition in form_registry.values():
        dimensions_json = (
            json.dumps(form_definition.dimensions)
            if form_definition.dimensions is not None
            else None
        )
        conn.execute(
            "INSERT INTO form (name, kind, unit_symbol, is_dimensionless, dimensions) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                form_definition.name,
                form_definition.kind.value
                if hasattr(form_definition.kind, "value")
                else str(form_definition.kind),
                form_definition.unit_symbol,
                1 if form_definition.is_dimensionless else 0,
                dimensions_json,
            ),
        )


def populate_concepts(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    form_registry: dict[str, FormDefinition],
) -> None:
    for seq, concept in enumerate(concepts, 1):
        data = concept.data
        logical_ids = concept_logical_ids(data)
        created = data.get("created_date")
        if created and not isinstance(created, str):
            created = str(created)
        modified = data.get("last_modified")
        if modified and not isinstance(modified, str):
            modified = str(modified)

        range_value = data.get("range")
        range_min = None
        range_max = None
        if isinstance(range_value, list) and len(range_value) >= 2:
            range_min = float(range_value[0])
            range_max = float(range_value[1])

        form_parameters = data.get("form_parameters")
        form_parameters_json = json.dumps(form_parameters) if form_parameters else None

        content_hash = concept_content_hash(data)

        form_name = data.get("form")
        form_definition = form_registry.get(form_name) if isinstance(form_name, str) else None
        is_dimensionless = 1 if (form_definition is not None and form_definition.is_dimensionless) else 0
        unit_symbol = form_definition.unit_symbol if form_definition is not None else None

        conn.execute(
            "INSERT INTO concept (id, primary_logical_id, logical_ids_json, version_id, content_hash, seq, canonical_name, status, domain, definition, "
            "kind_type, form, form_parameters, range_min, range_max, "
            "is_dimensionless, unit_symbol, "
            "created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                concept_artifact_id(data),
                concept_primary_logical_id(data),
                json.dumps(logical_ids),
                concept_version_id(data),
                content_hash,
                seq,
                data.get("canonical_name"),
                data.get("status"),
                data.get("domain"),
                data.get("definition"),
                form_definition.kind.value
                if form_definition is not None
                else kind_value_from_form_name(data.get("form")),
                data.get("form", ""),
                form_parameters_json,
                range_min,
                range_max,
                is_dimensionless,
                unit_symbol,
                created,
                modified,
            ),
        )


def populate_aliases(conn: sqlite3.Connection, concepts: list[LoadedEntry]) -> None:
    for concept in concepts:
        data = concept.data
        concept_id = concept_artifact_id(data)
        for alias in data.get("aliases", []) or []:
            conn.execute(
                "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
                (concept_id, alias.get("name"), alias.get("source")),
            )


def populate_relationships(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    concept_registry: dict[str, dict],
) -> None:
    for concept in concepts:
        data = concept.data
        source_id = concept_artifact_id(data)
        for relationship in data.get("relationships", []) or []:
            conditions = relationship.get("conditions", []) or []
            conditions_json = json.dumps(conditions) if conditions else None
            target_id = resolve_concept_reference(relationship.get("target"), concept_registry)
            conn.execute(
                "INSERT INTO relationship (source_id, type, target_id, conditions_cel, note) VALUES (?, ?, ?, ?, ?)",
                (
                    source_id,
                    relationship.get("type"),
                    target_id,
                    conditions_json,
                    relationship.get("note"),
                ),
            )
            conn.execute(
                "INSERT INTO relation_edge (source_kind, source_id, relation_type, target_kind, target_id, conditions_cel, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "concept",
                    source_id,
                    relationship.get("type"),
                    "concept",
                    target_id,
                    conditions_json,
                    relationship.get("note"),
                ),
            )


def populate_parameterizations(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    concept_registry: dict[str, dict],
) -> None:
    for concept in concepts:
        data = concept.data
        for parameterization in data.get("parameterization_relationships", []) or []:
            raw_inputs = parameterization.get("inputs", [])
            inputs = [
                resolve_concept_reference(input_id, concept_registry)
                if isinstance(input_id, str)
                else input_id
                for input_id in raw_inputs
            ]
            conditions = parameterization.get("conditions", []) or []
            conn.execute(
                "INSERT INTO parameterization (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    concept_artifact_id(data),
                    json.dumps(inputs),
                    parameterization.get("formula"),
                    parameterization.get("sympy"),
                    parameterization.get("exactness"),
                    json.dumps(conditions) if conditions else None,
                ),
            )


def populate_parameterization_groups(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
) -> None:
    concept_dicts: list[dict] = []
    for concept in concepts:
        concept_dicts.append(dict(concept.data))
    groups = build_groups(concept_dicts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            conn.execute(
                "INSERT INTO parameterization_group (concept_id, group_id) VALUES (?, ?)",
                (concept_id, group_id),
            )


def build_concept_fts_index(conn: sqlite3.Connection, concepts: list[LoadedEntry]) -> None:
    """Build the FTS5 index over concept names, aliases, definitions, and conditions."""
    conn.execute(
        """
        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        )
        """
    )

    for concept in concepts:
        data = concept.data
        concept_id = concept_artifact_id(data) or ""
        alias_names = [alias.get("name", "") for alias in data.get("aliases", []) or []]
        aliases_text = " ".join(alias_names)

        conditions_parts = []
        for relationship in data.get("relationships", []) or []:
            for condition in relationship.get("conditions", []) or []:
                conditions_parts.append(condition)
        for parameterization in data.get("parameterization_relationships", []) or []:
            for condition in parameterization.get("conditions", []) or []:
                conditions_parts.append(condition)
        conditions_text = " ".join(conditions_parts)

        conn.execute(
            "INSERT INTO concept_fts (concept_id, canonical_name, aliases, definition, conditions) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                concept_id,
                data.get("canonical_name", ""),
                aliases_text,
                data.get("definition", ""),
                conditions_text,
            ),
        )

"""Concept and form compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError

from propstore.core.concepts import ConceptRecord, LoadedConcept
from propstore.form_utils import (
    FormDefinition,
    kind_value_from_form_name,
    verify_form_algebra_dimensions,
)
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols


def _concept_symbol_candidates(record: ConceptRecord) -> tuple[str, ...]:
    return record.reference_keys()


def populate_form_algebra(
    conn: sqlite3.Connection,
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> None:
    """Derive form algebra from concept parameterizations and populate the table."""
    if not form_registry:
        return

    id_to_form: dict[str, str] = {}
    id_to_symbols: dict[str, tuple[str, ...]] = {}
    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        id_to_form[concept_id] = record.form
        id_to_symbols[concept_id] = _concept_symbol_candidates(record)

    seen: set[tuple[object, ...]] = set()

    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        output_form = id_to_form.get(concept_id)
        if not output_form:
            continue

        for parameterization in record.parameterizations:
            inputs = [str(input_id) for input_id in parameterization.inputs]
            if not inputs:
                continue

            input_forms: list[str] = []
            all_resolved = True
            for input_id in inputs:
                input_form = id_to_form.get(input_id)
                if not input_form:
                    all_resolved = False
                    break
                input_forms.append(input_form)
            if not all_resolved:
                continue

            sympy_str = parameterization.sympy
            operation = ""
            if sympy_str:
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
            if not operation:
                operation = parameterization.formula or ""

            dim_verified = 1
            if sympy_str and operation:
                output_fd = form_registry.get(output_form)
                input_fd_list = [form_registry.get(form_name) for form_name in input_forms]
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
            except AlgorithmParseError:
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
                    parameterization.formula or "",
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
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> None:
    for seq, concept in enumerate(concepts, 1):
        record = concept.record
        content_hash = record.version_id.removeprefix("sha256:")[:16]
        form_definition = form_registry.get(record.form)
        is_dimensionless = (
            1
            if (form_definition is not None and form_definition.is_dimensionless)
            else 0
        )
        unit_symbol = form_definition.unit_symbol if form_definition is not None else None

        form_parameters_json = (
            json.dumps(record.form_parameters)
            if record.form_parameters
            else None
        )

        range_min = None if record.range is None else record.range[0]
        range_max = None if record.range is None else record.range[1]

        conn.execute(
            "INSERT INTO concept (id, primary_logical_id, logical_ids_json, version_id, content_hash, seq, canonical_name, status, domain, definition, "
            "kind_type, form, form_parameters, range_min, range_max, "
            "is_dimensionless, unit_symbol, "
            "created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(record.artifact_id),
                record.primary_logical_id,
                json.dumps([logical_id.to_payload() for logical_id in record.logical_ids]),
                record.version_id,
                content_hash,
                seq,
                record.canonical_name,
                record.status.value,
                record.domain,
                record.definition,
                form_definition.kind.value
                if form_definition is not None
                else kind_value_from_form_name(record.form),
                record.form,
                form_parameters_json,
                range_min,
                range_max,
                is_dimensionless,
                unit_symbol,
                record.created_date,
                record.last_modified,
            ),
        )


def populate_aliases(conn: sqlite3.Connection, concepts: list[LoadedConcept]) -> None:
    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        for alias in record.aliases:
            conn.execute(
                "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
                (concept_id, alias.name, alias.source),
            )


def populate_relationships(
    conn: sqlite3.Connection,
    concepts: list[LoadedConcept],
) -> None:
    for concept in concepts:
        record = concept.record
        source_id = str(record.artifact_id)
        for relationship in record.relationships:
            conditions_json = (
                json.dumps(list(relationship.conditions))
                if relationship.conditions
                else None
            )
            target_id = str(relationship.target)
            conn.execute(
                "INSERT INTO relationship (source_id, type, target_id, conditions_cel, note) VALUES (?, ?, ?, ?, ?)",
                (
                    source_id,
                    relationship.relationship_type,
                    target_id,
                    conditions_json,
                    relationship.note,
                ),
            )
            conn.execute(
                "INSERT INTO relation_edge (source_kind, source_id, relation_type, target_kind, target_id, conditions_cel, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "concept",
                    source_id,
                    relationship.relationship_type,
                    "concept",
                    target_id,
                    conditions_json,
                    relationship.note,
                ),
            )


def populate_parameterizations(
    conn: sqlite3.Connection,
    concepts: list[LoadedConcept],
) -> None:
    for concept in concepts:
        record = concept.record
        output_id = str(record.artifact_id)
        for parameterization in record.parameterizations:
            inputs = [str(input_id) for input_id in parameterization.inputs]
            conditions_json = (
                json.dumps(list(parameterization.conditions))
                if parameterization.conditions
                else None
            )
            conn.execute(
                "INSERT INTO parameterization (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    output_id,
                    json.dumps(inputs),
                    parameterization.formula,
                    parameterization.sympy,
                    parameterization.exactness,
                    conditions_json,
                ),
            )


def populate_parameterization_groups(
    conn: sqlite3.Connection,
    concepts: list[LoadedConcept],
) -> None:
    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            conn.execute(
                "INSERT INTO parameterization_group (concept_id, group_id) VALUES (?, ?)",
                (concept_id, group_id),
            )


def build_concept_fts_index(conn: sqlite3.Connection, concepts: list[LoadedConcept]) -> None:
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
        record = concept.record
        alias_names = [alias.name for alias in record.aliases]
        aliases_text = " ".join(alias_names)

        conditions_parts: list[str] = []
        for relationship in record.relationships:
            conditions_parts.extend(relationship.conditions)
        for parameterization in record.parameterizations:
            conditions_parts.extend(parameterization.conditions)
        conditions_text = " ".join(conditions_parts)

        conn.execute(
            "INSERT INTO concept_fts (concept_id, canonical_name, aliases, definition, conditions) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                str(record.artifact_id),
                record.canonical_name,
                aliases_text,
                record.definition,
                conditions_text,
            ),
        )

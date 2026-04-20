"""Sidecar row compilation passes."""

from __future__ import annotations

import json

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError

from propstore.claims import claim_file_filename, claim_file_stage
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.dimensions import verify_form_algebra_dimensions
from propstore.families.concepts.stages import ConceptRecord, LoadedConcept
from propstore.families.forms.stages import (
    FormDefinition,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols
from propstore.sidecar.claim_utils import (
    collect_claim_reference_map,
    extract_deferred_stance_rows,
    prepare_claim_insert_row,
)
from propstore.sidecar.stages import (
    ClaimInsertRow,
    ClaimSidecarRows,
    ClaimStanceInsertRow,
    ConceptAliasInsertRow,
    ConceptFtsInsertRow,
    ConceptInsertRow,
    ConceptParameterizationGroupInsertRow,
    ConceptParameterizationInsertRow,
    ConceptRelationshipInsertRow,
    ConceptSidecarRows,
    FormAlgebraInsertRow,
    FormInsertRow,
    RelationEdgeInsertRow,
)


def _concept_symbol_candidates(record: ConceptRecord) -> tuple[str, ...]:
    return record.reference_keys()


def compile_concept_sidecar_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> ConceptSidecarRows:
    form_rows: list[FormInsertRow] = []
    concept_rows: list[ConceptInsertRow] = []
    alias_rows: list[ConceptAliasInsertRow] = []
    relationship_rows: list[ConceptRelationshipInsertRow] = []
    relation_edge_rows: list[RelationEdgeInsertRow] = []
    parameterization_rows: list[ConceptParameterizationInsertRow] = []
    parameterization_group_rows: list[ConceptParameterizationGroupInsertRow] = []
    form_algebra_rows: list[FormAlgebraInsertRow] = []
    concept_fts_rows: list[ConceptFtsInsertRow] = []

    for form_definition in form_registry.values():
        dimensions_json = (
            json.dumps(form_definition.dimensions)
            if form_definition.dimensions is not None
            else None
        )
        form_rows.append(
            FormInsertRow(
                (
                    form_definition.name,
                    form_definition.kind.value
                    if hasattr(form_definition.kind, "value")
                    else str(form_definition.kind),
                    form_definition.unit_symbol,
                    1 if form_definition.is_dimensionless else 0,
                    dimensions_json,
                )
            )
        )

    for seq, concept in enumerate(concepts, 1):
        record = concept.record
        content_hash = record.version_id.removeprefix("sha256:")[:16]
        form_definition = form_registry.get(record.form)
        is_dimensionless = (
            1
            if form_definition is not None and form_definition.is_dimensionless
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
        concept_id = str(record.artifact_id)

        concept_rows.append(
            ConceptInsertRow(
                (
                    concept_id,
                    record.primary_logical_id,
                    json.dumps(
                        [
                            logical_id.to_payload()
                            for logical_id in record.logical_ids
                        ]
                    ),
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
                )
            )
        )

        for alias in record.aliases:
            alias_rows.append(ConceptAliasInsertRow((concept_id, alias.name, alias.source)))

        for relationship in record.relationships:
            conditions_json = (
                json.dumps(list(relationship.conditions))
                if relationship.conditions
                else None
            )
            target_id = str(relationship.target)
            relationship_rows.append(
                ConceptRelationshipInsertRow(
                    (
                        concept_id,
                        relationship.relationship_type,
                        target_id,
                        conditions_json,
                        relationship.note,
                    )
                )
            )
            relation_edge_rows.append(
                RelationEdgeInsertRow(
                    (
                        "concept",
                        concept_id,
                        relationship.relationship_type,
                        "concept",
                        target_id,
                        conditions_json,
                        relationship.note,
                    )
                )
            )

        for parameterization in record.parameterizations:
            inputs = [str(input_id) for input_id in parameterization.inputs]
            conditions_json = (
                json.dumps(list(parameterization.conditions))
                if parameterization.conditions
                else None
            )
            parameterization_rows.append(
                ConceptParameterizationInsertRow(
                    (
                        concept_id,
                        json.dumps(inputs),
                        parameterization.formula,
                        parameterization.sympy,
                        parameterization.exactness,
                        conditions_json,
                    )
                )
            )

        alias_names = [alias.name for alias in record.aliases]
        conditions_parts: list[str] = []
        for relationship in record.relationships:
            conditions_parts.extend(relationship.conditions)
        for parameterization in record.parameterizations:
            conditions_parts.extend(parameterization.conditions)
        concept_fts_rows.append(
            ConceptFtsInsertRow(
                (
                    concept_id,
                    record.canonical_name,
                    " ".join(alias_names),
                    record.definition,
                    " ".join(conditions_parts),
                )
            )
        )

    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            parameterization_group_rows.append(
                ConceptParameterizationGroupInsertRow((concept_id, group_id))
            )

    form_algebra_rows.extend(_compile_form_algebra_rows(concepts, form_registry))

    return ConceptSidecarRows(
        form_rows=tuple(form_rows),
        concept_rows=tuple(concept_rows),
        alias_rows=tuple(alias_rows),
        relationship_rows=tuple(relationship_rows),
        relation_edge_rows=tuple(relation_edge_rows),
        parameterization_rows=tuple(parameterization_rows),
        parameterization_group_rows=tuple(parameterization_group_rows),
        form_algebra_rows=tuple(form_algebra_rows),
        concept_fts_rows=tuple(concept_fts_rows),
    )


def _compile_form_algebra_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> tuple[FormAlgebraInsertRow, ...]:
    if not form_registry:
        return ()

    id_to_form: dict[str, str] = {}
    id_to_symbols: dict[str, tuple[str, ...]] = {}
    for concept in concepts:
        record = concept.record
        concept_id = str(record.artifact_id)
        id_to_form[concept_id] = record.form
        id_to_symbols[concept_id] = _concept_symbol_candidates(record)

    seen: set[tuple[object, ...]] = set()
    rows: list[FormAlgebraInsertRow] = []

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
            rows.append(
                FormAlgebraInsertRow(
                    (
                        output_form,
                        json.dumps(input_forms),
                        operation,
                        concept_id,
                        parameterization.formula or "",
                        dim_verified,
                    )
                )
            )

    return tuple(rows)


def compile_claim_sidecar_rows(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: dict,
    *,
    form_registry: dict | None = None,
) -> ClaimSidecarRows:
    claim_seq = 0
    claim_rows: list[ClaimInsertRow] = []
    stance_rows: list[ClaimStanceInsertRow] = []
    claim_reference_map = collect_claim_reference_map(
        claim_bundle.normalized_claim_files
    )
    file_stage_by_filename: dict[str, str | None] = {
        claim_file_filename(claim_file): claim_file_stage(claim_file)
        for claim_file in claim_bundle.normalized_claim_files
    }

    for semantic_file in claim_bundle.semantic_files:
        file_stage = file_stage_by_filename.get(
            claim_file_filename(semantic_file.normalized_entry)
        )
        for semantic_claim in semantic_file.claims:
            claim_seq += 1
            row = prepare_claim_insert_row(
                semantic_claim,
                semantic_claim.source_paper,
                claim_seq=claim_seq,
                concept_registry=concept_registry,
                form_registry=form_registry,
            )
            if file_stage is not None:
                row["stage"] = file_stage
            claim_rows.append(ClaimInsertRow(row))
            stance_rows.extend(
                ClaimStanceInsertRow(values)
                for values in extract_deferred_stance_rows(
                    semantic_claim,
                    claim_reference_map,
                    source_paper=semantic_claim.source_paper,
                )
            )

    return ClaimSidecarRows(
        claim_rows=tuple(claim_rows),
        stance_rows=tuple(stance_rows),
    )

"""Sidecar row compilation passes."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError
from quire.projections import ProjectionRow

from propstore.claims import (
    ClaimFileEntry,
    claim_file_claims,
    claim_file_filename,
    claim_file_stage,
)
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo, with_standard_synthetic_bindings
from propstore.dimensions import verify_form_algebra_dimensions
from propstore.families.concepts.stages import ConceptRecord, LoadedConcept
from propstore.families.concepts.declaration import (
    ALIAS_PROJECTION,
    CONCEPT_PROJECTION,
    ConceptRelationshipProjectionRow,
    ConceptSidecarRows,
    FORM_ALGEBRA_PROJECTION,
    FORM_PROJECTION,
    PARAMETERIZATION_GROUP_PROJECTION,
    PARAMETERIZATION_PROJECTION,
)
from propstore.families.contexts.stages import LoadedContext, loaded_contexts_to_lifting_system
from propstore.families.contexts.declaration import (
    ContextSidecarRows,
    compile_context_sidecar_rows,
)
from propstore.families.claims.stages import (
    ClaimCheckedBundle,
    ClaimSidecarRows,
    RawIdQuarantineRecord,
    RawIdQuarantineSidecarRows,
)
from propstore.families.claims.references import (
    build_claim_file_reference_index,
)
from propstore.families.forms.stages import (
    FormDefinition,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols
from propstore.families.claims.storage import (
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_insert_row,
    prepare_claim_concept_link_rows,
)
from propstore.families.claims.declaration import (
    CLAIM_ALGORITHM_PAYLOAD_PROJECTION,
    CLAIM_CONCEPT_LINK_PROJECTION,
    CLAIM_CORE_PROJECTION,
    CLAIM_NUMERIC_PAYLOAD_PROJECTION,
    CLAIM_TEXT_PAYLOAD_PROJECTION,
    CONFLICT_WITNESS_PROJECTION,
    compile_authored_justification_sidecar_rows_with_diagnostics,
)
from propstore.families.diagnostics.declaration import (
    BUILD_DIAGNOSTICS_PROJECTION,
    QuarantineDiagnostic,
)
from propstore.families.micropublications.declaration import (
    MicropublicationSidecarRows,
    compile_micropublication_sidecar_rows_with_diagnostics,
)
from propstore.families.relations.declaration import (
    RELATION_EDGE_PROJECTION,
    claim_stance_projection_row,
    compile_authored_stance_sidecar_rows_with_diagnostics,
)
from propstore.families.sources.declaration import (
    SourceProjectionRow,
    compile_source_sidecar_rows,
)

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.families.documents.justifications import JustificationDocument
    from propstore.families.documents.micropubs import MicropublicationDocument
    from propstore.families.documents.sources import SourceDocument
    from propstore.families.documents.stances import StanceDocument


@dataclass(frozen=True)
class RepositoryCheckedBundle:
    concepts: list[LoadedConcept]
    form_registry: dict[str, FormDefinition]
    context_files: tuple[LoadedContext, ...]
    context_ids: frozenset[str]
    compilation_context: "CompilationContext"
    concept_registry: dict
    claim_checked_bundle: ClaimCheckedBundle | None
    normalized_claim_files: tuple[ClaimFileEntry, ...] | None


@dataclass(frozen=True)
class SidecarBuildPlan:
    source_rows: tuple[SourceProjectionRow, ...]
    concept_rows: ConceptSidecarRows
    context_rows: ContextSidecarRows
    claim_rows: ClaimSidecarRows | None
    raw_id_quarantine_rows: RawIdQuarantineSidecarRows
    conflict_rows: tuple[ProjectionRow, ...]
    micropublication_rows: MicropublicationSidecarRows
    stance_rows: tuple[ProjectionRow, ...]
    justification_rows: tuple[ProjectionRow, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


def _concept_symbol_candidates(record: ConceptRecord) -> tuple[str, ...]:
    return record.reference_keys()


def compile_concept_sidecar_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptSidecarRows:
    form_rows: list[ProjectionRow] = []
    concept_rows: list[ProjectionRow] = []
    alias_rows: list[ProjectionRow] = []
    relationship_rows: list[ConceptRelationshipProjectionRow] = []
    relation_edge_rows: list[ProjectionRow] = []
    parameterization_rows: list[ProjectionRow] = []
    parameterization_group_rows: list[ProjectionRow] = []
    form_algebra_rows: list[ProjectionRow] = []

    for form_definition in form_registry.values():
        dimensions_json = (
            json.dumps(form_definition.dimensions)
            if form_definition.dimensions is not None
            else None
        )
        form_rows.append(
            FORM_PROJECTION.row(
                name=form_definition.name,
                kind=form_definition.kind.value
                if hasattr(form_definition.kind, "value")
                else str(form_definition.kind),
                unit_symbol=form_definition.unit_symbol,
                is_dimensionless=1 if form_definition.is_dimensionless else 0,
                dimensions=dimensions_json,
            )
        )

    condition_registry = with_standard_synthetic_bindings(cel_registry)

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
            CONCEPT_PROJECTION.row(
                id=concept_id,
                primary_logical_id=record.primary_logical_id or "",
                logical_ids_json=json.dumps(
                    [logical_id.to_payload() for logical_id in record.logical_ids]
                ),
                version_id=record.version_id,
                content_hash=content_hash,
                seq=seq,
                canonical_name=record.canonical_name,
                status=record.status.value,
                domain=record.domain,
                definition=record.definition,
                kind_type=form_definition.kind.value
                if form_definition is not None
                else kind_value_from_form_name(record.form),
                form=record.form,
                form_parameters=form_parameters_json,
                range_min=range_min,
                range_max=range_max,
                is_dimensionless=is_dimensionless,
                unit_symbol=unit_symbol,
                created_date=record.created_date,
                last_modified=record.last_modified,
            )
        )

        for alias in record.aliases:
            alias_rows.append(
                ALIAS_PROJECTION.row(
                    concept_id=concept_id,
                    alias_name=alias.name,
                    source=alias.source,
                )
            )

        for relationship in record.relationships:
            conditions_json = (
                json.dumps(list(relationship.conditions))
                if relationship.conditions
                else None
            )
            target_id = str(relationship.target)
            relationship_rows.append(
                ConceptRelationshipProjectionRow(
                    source_id=concept_id,
                    relationship_type=relationship.relationship_type,
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )
            relation_edge_rows.append(
                RELATION_EDGE_PROJECTION.row(
                    source_kind="concept",
                    source_id=concept_id,
                    relation_type=relationship.relationship_type,
                    target_kind="concept",
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )

        for parameterization in record.parameterizations:
            if parameterization.formula is None:
                raise ValueError(f"Parameterization for {concept_id} is missing formula")
            if parameterization.exactness is None:
                raise ValueError(f"Parameterization for {concept_id} is missing exactness")
            inputs = [str(input_id) for input_id in parameterization.inputs]
            conditions_json = (
                json.dumps(list(parameterization.conditions))
                if parameterization.conditions
                else None
            )
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(
                        checked_condition_set(
                            check_condition_ir(condition, condition_registry)
                            for condition in parameterization.conditions
                        )
                    ),
                    sort_keys=True,
                )
                if parameterization.conditions
                else None
            )
            parameterization_rows.append(
                PARAMETERIZATION_PROJECTION.row(
                    output_concept_id=concept_id,
                    concept_ids=json.dumps(inputs),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=str(parameterization.exactness),
                    conditions_cel=conditions_json,
                    conditions_ir=conditions_ir,
                )
            )

    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            parameterization_group_rows.append(
                PARAMETERIZATION_GROUP_PROJECTION.row(
                    concept_id=concept_id,
                    group_id=group_id,
                )
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
    )


def _compile_form_algebra_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> tuple[ProjectionRow, ...]:
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
    rows: list[ProjectionRow] = []

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
                FORM_ALGEBRA_PROJECTION.row(
                    output_form=output_form,
                    input_forms=json.dumps(input_forms),
                    operation=operation,
                    source_concept_id=concept_id,
                    source_formula=parameterization.formula or "",
                    dim_verified=dim_verified,
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
    claim_core_rows: list[ProjectionRow] = []
    numeric_payload_rows: list[ProjectionRow] = []
    text_payload_rows: list[ProjectionRow] = []
    algorithm_payload_rows: list[ProjectionRow] = []
    claim_link_rows: list[ProjectionRow] = []
    stance_rows: list[ProjectionRow] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    claim_index = build_claim_file_reference_index(
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
            claim_core_rows.append(
                CLAIM_CORE_PROJECTION.row(
                    id=row["id"],
                    primary_logical_id=row["primary_logical_id"],
                    logical_ids_json=row["logical_ids_json"],
                    version_id=row["version_id"],
                    content_hash=row.get("content_hash") or "",
                    seq=row["seq"],
                    type=row["type"],
                    target_concept=row["target_concept"],
                    source_slug=row["source_slug"],
                    source_paper=row["source_paper"],
                    provenance_page=row["provenance_page"],
                    provenance_json=row["provenance_json"],
                    context_id=row["context_id"],
                    premise_kind=row.get("premise_kind") or "ordinary",
                    branch=row.get("branch"),
                    build_status=row.get("build_status") or "ingested",
                    stage=row.get("stage"),
                    promotion_status=row.get("promotion_status"),
                )
            )
            numeric_payload_rows.append(
                CLAIM_NUMERIC_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    value=row["value"],
                    lower_bound=row["lower_bound"],
                    upper_bound=row["upper_bound"],
                    uncertainty=row["uncertainty"],
                    uncertainty_type=row["uncertainty_type"],
                    sample_size=row["sample_size"],
                    unit=row["unit"],
                    value_si=row["value_si"],
                    lower_bound_si=row["lower_bound_si"],
                    upper_bound_si=row["upper_bound_si"],
                )
            )
            text_payload_rows.append(
                CLAIM_TEXT_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    conditions_cel=row["conditions_cel"],
                    conditions_ir=row["conditions_ir"],
                    statement=row["statement"],
                    expression=row["expression"],
                    sympy_generated=row["sympy_generated"],
                    sympy_error=row["sympy_error"],
                    name=row["name"],
                    measure=row["measure"],
                    listener_population=row["listener_population"],
                    methodology=row["methodology"],
                    notes=row["notes"],
                    description=row["description"],
                    auto_summary=row["auto_summary"],
                )
            )
            algorithm_payload_rows.append(
                CLAIM_ALGORITHM_PAYLOAD_PROJECTION.row(
                    claim_id=row["id"],
                    body=row["body"],
                    canonical_ast=row["canonical_ast"],
                    variables_json=row["variables_json"],
                    algorithm_stage=row["algorithm_stage"],
                )
            )
            for values in prepare_claim_concept_link_rows(semantic_claim):
                claim_link_rows.append(
                    CLAIM_CONCEPT_LINK_PROJECTION.row(
                        claim_id=values[0],
                        concept_id=values[1],
                        role=values[2],
                        ordinal=values[3],
                        binding_name=values[4],
                    )
                )
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_index,
                )
            )
            stance_rows.extend(
                claim_stance_projection_row(values)
                for values in deferred_stance_rows
            )
            quarantine_diagnostics.extend(deferred_stance_diagnostics)

    return ClaimSidecarRows(
        claim_core_rows=tuple(claim_core_rows),
        numeric_payload_rows=tuple(numeric_payload_rows),
        text_payload_rows=tuple(text_payload_rows),
        algorithm_payload_rows=tuple(algorithm_payload_rows),
        claim_link_rows=tuple(claim_link_rows),
        stance_rows=tuple(stance_rows),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ProjectionRow, ...]:
    conflict_claims = conflict_claims_from_claim_files(claim_files)
    records = detect_conflicts(
        conflict_claims,
        concept_registry,
        cel_registry,
        lifting_system=lifting_system,
    )
    records.extend(
        detect_transitive_conflicts(
            conflict_claims,
            concept_registry,
            lifting_system=lifting_system,
        )
    )
    return tuple(
        CONFLICT_WITNESS_PROJECTION.row(
            concept_id=record.concept_id,
            claim_a_id=record.claim_a_id,
            claim_b_id=record.claim_b_id,
            warning_class=record.warning_class.value,
            conditions_a=json.dumps(record.conditions_a),
            conditions_b=json.dumps(record.conditions_b),
            value_a=record.value_a,
            value_b=record.value_b,
            derivation_chain=record.derivation_chain,
        )
        for record in records
    )


def compile_raw_id_quarantine_sidecar_rows(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineSidecarRows:
    claim_rows: list[ProjectionRow] = []
    diagnostic_rows: list[ProjectionRow] = []

    for record in records:
        claim_rows.append(
            CLAIM_CORE_PROJECTION.row(
                id=record.synthetic_id,
                primary_logical_id="",
                logical_ids_json="[]",
                version_id="",
                content_hash="",
                seq=record.seq,
                type="quarantine",
                target_concept=None,
                source_slug=record.source_paper,
                source_paper=record.source_paper,
                provenance_page=0,
                provenance_json=None,
                context_id=None,
                premise_kind="ordinary",
                branch=None,
                build_status="blocked",
                stage=None,
                promotion_status=None,
            )
        )
        diagnostic_rows.append(
            BUILD_DIAGNOSTICS_PROJECTION.row(
                claim_id=record.synthetic_id,
                source_kind="claim",
                source_ref=record.raw_id,
                diagnostic_kind="raw_id_input",
                severity="error",
                blocking=1,
                message=record.message,
                file=record.filename,
                detail_json=record.detail_json,
            )
        )

    return RawIdQuarantineSidecarRows(
        claim_rows=tuple(claim_rows),
        diagnostic_rows=tuple(diagnostic_rows),
    )


def compile_sidecar_build_plan(
    repository_checked_bundle: RepositoryCheckedBundle,
    *,
    source_entries: Iterable[tuple[str, SourceDocument]],
    stance_entries: Iterable[tuple[str, StanceDocument]],
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
) -> SidecarBuildPlan:
    claim_rows: ClaimSidecarRows | None = None
    raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(())
    conflict_rows: tuple[ProjectionRow, ...] = ()
    stance_rows: tuple[ProjectionRow, ...] = ()
    justification_rows: tuple[ProjectionRow, ...] = ()
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...] = ()
    claim_index = build_claim_file_reference_index(())

    if repository_checked_bundle.normalized_claim_files is not None:
        checked_claims = repository_checked_bundle.claim_checked_bundle
        if checked_claims is None:
            raise ValueError("checked claim bundle is required to populate claims")
        normalized_claim_files = repository_checked_bundle.normalized_claim_files
        claim_index = build_claim_file_reference_index(normalized_claim_files)
        claim_rows = compile_claim_sidecar_rows(
            checked_claims.bundle,
            repository_checked_bundle.concept_registry,
            form_registry=repository_checked_bundle.form_registry,
        )
        quarantine_diagnostics = claim_rows.quarantine_diagnostics
        raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(
            checked_claims.raw_id_quarantine_records
        )
        lifting_system = (
            loaded_contexts_to_lifting_system(
                list(repository_checked_bundle.context_files)
            )
            if repository_checked_bundle.context_files
            else None
        )
        conflict_rows = compile_conflict_sidecar_rows(
            list(normalized_claim_files),
            repository_checked_bundle.concept_registry,
            dict(repository_checked_bundle.compilation_context.cel_registry),
            lifting_system=lifting_system,
        )
        stance_rows, stance_quarantine_diagnostics = (
            compile_authored_stance_sidecar_rows_with_diagnostics(
                stance_entries,
                claim_index,
            )
        )
        justification_rows, justification_quarantine_diagnostics = (
            compile_authored_justification_sidecar_rows_with_diagnostics(
                justification_entries,
                claim_index,
            )
        )
        quarantine_diagnostics = (
            quarantine_diagnostics
            + stance_quarantine_diagnostics
            + justification_quarantine_diagnostics
        )

    micropublication_rows, micropublication_quarantine_diagnostics = (
        compile_micropublication_sidecar_rows_with_diagnostics(
            micropub_entries,
            claim_index,
        )
    )
    quarantine_diagnostics = (
        quarantine_diagnostics + micropublication_quarantine_diagnostics
    )

    return SidecarBuildPlan(
        source_rows=compile_source_sidecar_rows(source_entries),
        concept_rows=compile_concept_sidecar_rows(
            repository_checked_bundle.concepts,
            repository_checked_bundle.form_registry,
            dict(repository_checked_bundle.compilation_context.cel_registry),
        ),
        context_rows=compile_context_sidecar_rows(
            repository_checked_bundle.context_files,
        ),
        claim_rows=claim_rows,
        raw_id_quarantine_rows=raw_id_quarantine_rows,
        conflict_rows=conflict_rows,
        micropublication_rows=micropublication_rows,
        stance_rows=stance_rows,
        justification_rows=justification_rows,
        quarantine_diagnostics=quarantine_diagnostics,
    )

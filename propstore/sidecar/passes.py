"""Sidecar row compilation passes."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Sequence

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError

from propstore.claims import (
    ClaimFileEntry,
    claim_file_claims,
    claim_file_filename,
    claim_file_stage,
)
from propstore.context_lifting import IstProposition, LiftedAssertion
from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts
from propstore.conflict_detector.collectors import conflict_claims_from_claim_files
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.dimensions import verify_form_algebra_dimensions
from propstore.families.concepts.stages import ConceptRecord, LoadedConcept
from propstore.families.contexts.stages import (
    LoadedContext,
    coerce_loaded_contexts,
    loaded_contexts_to_lifting_system,
)
from propstore.families.documents.micropubs import MicropublicationsFileDocument
from propstore.families.documents.sources import (
    SourceDocument,
    SourceJustificationsDocument,
)
from propstore.families.claims.stages import RawIdQuarantineRecord
from propstore.families.documents.stances import StanceFileDocument
from propstore.families.forms.stages import (
    FormDefinition,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols
from propstore.sidecar.claim_utils import (
    collect_claim_reference_map,
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_insert_row,
    prepare_claim_concept_link_rows,
)
from propstore.sidecar.stages import (
    ClaimInsertRow,
    ClaimConceptLinkInsertRow,
    ClaimFtsInsertRow,
    ClaimSidecarRows,
    ClaimStanceInsertRow,
    ConceptAliasInsertRow,
    ConceptFtsInsertRow,
    ContextAssumptionInsertRow,
    ContextInsertRow,
    ContextLiftingMaterializationInsertRow,
    ContextLiftingRuleInsertRow,
    ContextSidecarRows,
    ConceptInsertRow,
    ConceptParameterizationGroupInsertRow,
    ConceptParameterizationInsertRow,
    ConceptRelationshipInsertRow,
    ConceptSidecarRows,
    ConflictWitnessInsertRow,
    FormAlgebraInsertRow,
    FormInsertRow,
    JustificationInsertRow,
    MicropublicationClaimInsertRow,
    MicropublicationInsertRow,
    MicropublicationSidecarRows,
    BuildDiagnosticInsertRow,
    RawIdQuarantineClaimInsertRow,
    RawIdQuarantineSidecarRows,
    QuarantineDiagnostic,
    RelationEdgeInsertRow,
    RepositoryCheckedBundle,
    SidecarBuildPlan,
    SourceInsertRow,
    SourceSidecarRows,
)
from propstore.sidecar.claim_utils import (
    coerce_stance_resolution,
    resolution_opinion_columns,
    resolve_claim_reference,
)
from propstore.stances import VALID_STANCE_TYPES


def _opinion_json(opinion) -> str | None:
    if opinion is None:
        return None
    return json.dumps(
        {
            "b": opinion.b,
            "d": opinion.d,
            "u": opinion.u,
            "a": opinion.a,
        },
        sort_keys=True,
    )


def _concept_symbol_candidates(record: ConceptRecord) -> tuple[str, ...]:
    return record.reference_keys()


def compile_source_sidecar_rows(
    sources: Iterable[tuple[str, SourceDocument]],
) -> SourceSidecarRows:
    rows: list[SourceInsertRow] = []
    for slug, source_doc in sources:
        origin = source_doc.origin
        trust = source_doc.trust
        rows.append(
            SourceInsertRow(
                (
                    slug,
                    str(source_doc.id or slug),
                    source_doc.kind.value,
                    origin.type.value,
                    origin.value,
                    origin.retrieved,
                    origin.content_ref,
                    _opinion_json(trust.prior_base_rate),
                    None
                    if trust.quality is None
                    else json.dumps(trust.quality.to_payload()),
                    None
                    if not trust.derived_from
                    else json.dumps(list(trust.derived_from)),
                    source_doc.artifact_code,
                )
            )
        )
    return SourceSidecarRows(source_rows=tuple(rows))


def compile_context_sidecar_rows(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> ContextSidecarRows:
    context_rows: list[ContextInsertRow] = []
    assumption_rows: list[ContextAssumptionInsertRow] = []
    lifting_rule_rows: list[ContextLiftingRuleInsertRow] = []

    for context in coerce_loaded_contexts(contexts):
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_rows.append(
            ContextInsertRow(
                (
                    context_id,
                    record.name or "",
                    record.description,
                    json.dumps(dict(record.parameters), sort_keys=True)
                    if record.parameters
                    else None,
                    record.perspective,
                )
            )
        )

        for seq, assumption in enumerate(record.assumptions, 1):
            assumption_rows.append(
                ContextAssumptionInsertRow((context_id, assumption, seq))
            )

        for rule in record.lifting_rules:
            lifting_rule_rows.append(
                ContextLiftingRuleInsertRow(
                    (
                        rule.id,
                        str(rule.source.id),
                        str(rule.target.id),
                        json.dumps(list(rule.conditions), sort_keys=True)
                        if rule.conditions
                        else None,
                        rule.mode.value,
                        rule.justification,
                    )
                )
            )

    materialization_rows = ()
    if authored_ist_assertions:
        materialization_rows = compile_context_lifting_materialization_rows(
            loaded_contexts_to_lifting_system(contexts).materialize_lifted_assertions(
                tuple(authored_ist_assertions)
            )
        )

    return ContextSidecarRows(
        context_rows=tuple(context_rows),
        assumption_rows=tuple(assumption_rows),
        lifting_rule_rows=tuple(lifting_rule_rows),
        lifting_materialization_rows=materialization_rows,
    )


def compile_context_lifting_materialization_rows(
    materializations: Sequence[LiftedAssertion],
) -> tuple[ContextLiftingMaterializationInsertRow, ...]:
    rows: list[ContextLiftingMaterializationInsertRow] = []
    for materialization in materializations:
        rows.append(
            ContextLiftingMaterializationInsertRow(
                (
                    materialization.rule_id,
                    str(materialization.source_context.id),
                    str(materialization.target_context.id),
                    materialization.proposition_id,
                    materialization.status.value,
                    materialization.exception_id,
                    json.dumps(materialization.provenance, sort_keys=True),
                )
            )
        )
    return tuple(rows)


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
    claim_link_rows: list[ClaimConceptLinkInsertRow] = []
    stance_rows: list[ClaimStanceInsertRow] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
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
            claim_link_rows.extend(
                ClaimConceptLinkInsertRow(values)
                for values in prepare_claim_concept_link_rows(semantic_claim)
            )
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_reference_map,
                    source_paper=semantic_claim.source_paper,
                )
            )
            stance_rows.extend(
                ClaimStanceInsertRow(values)
                for values in deferred_stance_rows
            )
            quarantine_diagnostics.extend(deferred_stance_diagnostics)

    return ClaimSidecarRows(
        claim_rows=tuple(claim_rows),
        claim_link_rows=tuple(claim_link_rows),
        stance_rows=tuple(stance_rows),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_claim_reference_map(
    claim_files: Sequence[ClaimFileEntry],
) -> dict[str, str]:
    return collect_claim_reference_map(claim_files)


def compile_authored_stance_sidecar_rows(
    stance_entries: Iterable[tuple[str, StanceFileDocument]],
    claim_reference_map: dict[str, str],
) -> tuple[ClaimStanceInsertRow, ...]:
    rows, diagnostics = _compile_authored_stance_sidecar_rows_with_diagnostics(
        stance_entries,
        claim_reference_map,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_authored_stance_sidecar_rows_with_diagnostics(
    stance_entries: Iterable[tuple[str, StanceFileDocument]],
    claim_reference_map: dict[str, str],
) -> tuple[tuple[ClaimStanceInsertRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_reference_map.values())
    rows: list[ClaimStanceInsertRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, data in stance_entries:
        source_claim = resolve_claim_reference(
            data.source_claim,
            claim_reference_map,
        ) or ""
        if source_claim not in valid_claims:
            message = (
                f"stance file {filename} references nonexistent source claim "
                f"'{source_claim}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=source_claim or data.source_claim or filename,
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        for index, stance in enumerate(data.stances, start=1):
            stance_payload = stance.to_payload()
            target = resolve_claim_reference(
                stance.target or "",
                claim_reference_map,
            ) or ""
            stance_type = stance_payload.get("type") or ""
            if target not in valid_claims:
                message = (
                    f"stance file {filename} references nonexistent target claim "
                    f"'{target}'"
                )
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=target or stance.target or filename,
                        kind="stance",
                        diagnostic_kind="stance_validation",
                        message=message,
                        file=filename,
                    )
                )
                continue
            if stance_type not in VALID_STANCE_TYPES:
                raise ValueError(
                    f"stance file {filename} uses unrecognized stance type "
                    f"'{stance_type}'"
                )

            resolution = coerce_stance_resolution(
                stance_payload.get("resolution"),
                f"stance file {filename} stance #{index}",
            )
            opinion_columns = resolution_opinion_columns(resolution)
            rows.append(
                ClaimStanceInsertRow(
                    (
                        source_claim,
                        target,
                        stance_type,
                        stance.target_justification_id,
                        stance.strength,
                        stance.conditions_differ,
                        stance.note,
                        resolution.get("method"),
                        resolution.get("model"),
                        resolution.get("embedding_model"),
                        resolution.get("embedding_distance"),
                        resolution.get("pass_number"),
                        resolution.get("confidence"),
                        opinion_columns[0],
                        opinion_columns[1],
                        opinion_columns[2],
                        opinion_columns[3],
                    )
                )
            )
    return tuple(rows), tuple(diagnostics)


def compile_authored_justification_sidecar_rows(
    justification_entries: Iterable[tuple[str, SourceJustificationsDocument]],
    claim_reference_map: dict[str, str],
) -> tuple[JustificationInsertRow, ...]:
    rows, diagnostics = _compile_authored_justification_sidecar_rows_with_diagnostics(
        justification_entries,
        claim_reference_map,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_authored_justification_sidecar_rows_with_diagnostics(
    justification_entries: Iterable[tuple[str, SourceJustificationsDocument]],
    claim_reference_map: dict[str, str],
) -> tuple[tuple[JustificationInsertRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_reference_map.values())
    rows: list[JustificationInsertRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, data in justification_entries:
        for index, justification in enumerate(data.justifications, start=1):
            justification_payload = justification.to_payload()
            justification_id = justification.id
            conclusion = resolve_claim_reference(
                justification.conclusion,
                claim_reference_map,
            )
            if not isinstance(justification_id, str) or not justification_id:
                raise ValueError(
                    f"justification file {filename} entry #{index} missing id"
                )
            if not isinstance(conclusion, str) or conclusion not in valid_claims:
                message = (
                    f"justification file {filename} entry #{index} references "
                    f"nonexistent conclusion '{conclusion}'"
                )
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=conclusion or justification.conclusion or filename,
                        kind="justification",
                        diagnostic_kind="justification_validation",
                        message=message,
                        file=filename,
                    )
                )
                continue
            resolved_premises: list[str] = []
            missing_premise_ref: str | None = None
            for premise in justification.premises:
                resolved_premise = resolve_claim_reference(premise, claim_reference_map)
                if (
                    not isinstance(resolved_premise, str)
                    or resolved_premise not in valid_claims
                ):
                    if isinstance(resolved_premise, str) and resolved_premise:
                        missing_premise_ref = resolved_premise
                    elif isinstance(premise, str) and premise:
                        missing_premise_ref = premise
                    else:
                        missing_premise_ref = filename
                    break
                resolved_premises.append(resolved_premise)
            if missing_premise_ref is not None:
                message = (
                    f"justification file {filename} entry #{index} references "
                    f"nonexistent premise '{missing_premise_ref}'"
                )
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=missing_premise_ref,
                        kind="justification",
                        diagnostic_kind="justification_validation",
                        message=message,
                        file=filename,
                    )
                )
                continue

            provenance = justification_payload.get("provenance")
            attack_target = justification_payload.get("attack_target")
            provenance_payload: dict[str, object] = {}
            if isinstance(provenance, dict):
                provenance_payload.update(provenance)
            if isinstance(attack_target, dict):
                provenance_payload["attack_target"] = attack_target

            rows.append(
                JustificationInsertRow(
                    (
                        justification_id,
                        str(justification.rule_kind or "reported_claim"),
                        conclusion,
                        json.dumps(resolved_premises),
                        None,
                        None,
                        json.dumps(provenance_payload)
                        if provenance_payload
                        else None,
                        str(justification.rule_strength or "defeasible"),
                    )
                )
            )
    return tuple(rows), tuple(diagnostics)


def compile_conflict_sidecar_rows(
    claim_files: Sequence[ClaimFileEntry],
    concept_registry: dict,
    cel_registry: dict,
    lifting_system=None,
) -> tuple[ConflictWitnessInsertRow, ...]:
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
        ConflictWitnessInsertRow(
            (
                record.concept_id,
                record.claim_a_id,
                record.claim_b_id,
                record.warning_class.value,
                json.dumps(record.conditions_a),
                json.dumps(record.conditions_b),
                record.value_a,
                record.value_b,
                record.derivation_chain,
            )
        )
        for record in records
    )


def compile_claim_fts_rows(
    claim_files: Sequence[ClaimFileEntry],
) -> tuple[ClaimFtsInsertRow, ...]:
    rows: list[ClaimFtsInsertRow] = []
    for claim_file in claim_files:
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id
            if not isinstance(claim_id, str) or not claim_id:
                continue
            rows.append(
                ClaimFtsInsertRow(
                    (
                        claim_id,
                        claim.statement or "",
                        " ".join(list(claim.conditions)),
                        claim.expression or "",
                    )
                )
            )
    return tuple(rows)


def compile_raw_id_quarantine_sidecar_rows(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineSidecarRows:
    claim_rows: list[RawIdQuarantineClaimInsertRow] = []
    diagnostic_rows: list[BuildDiagnosticInsertRow] = []

    for record in records:
        claim_rows.append(
            RawIdQuarantineClaimInsertRow(
                (
                    record.synthetic_id,
                    "",
                    "[]",
                    "",
                    "",
                    record.seq,
                    "quarantine",
                    None,
                    record.source_paper,
                    record.source_paper,
                    0,
                    None,
                    None,
                    "ordinary",
                    None,
                    "blocked",
                    None,
                    None,
                )
            )
        )
        diagnostic_rows.append(
            BuildDiagnosticInsertRow(
                (
                    record.synthetic_id,
                    "claim",
                    record.raw_id,
                    "raw_id_input",
                    "error",
                    1,
                    record.message,
                    record.filename,
                    record.detail_json,
                )
            )
        )

    return RawIdQuarantineSidecarRows(
        claim_rows=tuple(claim_rows),
        diagnostic_rows=tuple(diagnostic_rows),
    )


def compile_micropublication_sidecar_rows(
    micropub_files: Iterable[tuple[str, MicropublicationsFileDocument]],
    claim_reference_map: dict[str, str],
) -> MicropublicationSidecarRows:
    rows, diagnostics = _compile_micropublication_sidecar_rows_with_diagnostics(
        micropub_files,
        claim_reference_map,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_micropublication_sidecar_rows_with_diagnostics(
    micropub_files: Iterable[tuple[str, MicropublicationsFileDocument]],
    claim_reference_map: dict[str, str],
) -> tuple[MicropublicationSidecarRows, tuple[QuarantineDiagnostic, ...]]:
    valid_claim_ids = set(claim_reference_map.values())
    micropublication_rows: list[MicropublicationInsertRow] = []
    claim_rows: list[MicropublicationClaimInsertRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, document in sorted(micropub_files, key=lambda item: item[0]):
        for micropub in document.micropubs:
            resolved_claims: list[str] = []
            missing_claim_ref: str | None = None
            for claim_id in micropub.claims:
                resolved_claim = resolve_claim_reference(claim_id, claim_reference_map)
                if (
                    not isinstance(resolved_claim, str)
                    or resolved_claim not in valid_claim_ids
                ):
                    if isinstance(resolved_claim, str) and resolved_claim:
                        missing_claim_ref = resolved_claim
                    elif isinstance(claim_id, str) and claim_id:
                        missing_claim_ref = claim_id
                    else:
                        missing_claim_ref = micropub.artifact_id
                    break
                resolved_claims.append(resolved_claim)
            if missing_claim_ref is not None:
                message = (
                    f"micropublication {micropub.artifact_id} references "
                    f"nonexistent claim '{missing_claim_ref}'"
                )
                diagnostics.append(
                    QuarantineDiagnostic(
                        artifact_id=missing_claim_ref,
                        kind="micropublication",
                        diagnostic_kind="micropublication_validation",
                        message=message,
                        file=filename,
                    )
                )
                continue

            micropublication_rows.append(
                MicropublicationInsertRow(
                    (
                        micropub.artifact_id,
                        str(micropub.context.id),
                        json.dumps(list(micropub.assumptions), sort_keys=True),
                        json.dumps(
                            [item.to_payload() for item in micropub.evidence],
                            sort_keys=True,
                        ),
                        None if micropub.stance is None else micropub.stance.value,
                        (
                            None
                            if micropub.provenance is None
                            else json.dumps(
                                micropub.provenance.to_payload(),
                                sort_keys=True,
                            )
                        ),
                        micropub.source,
                    )
                )
            )
            for seq, claim_id in enumerate(resolved_claims, start=1):
                assert claim_id is not None
                claim_rows.append(
                    MicropublicationClaimInsertRow(
                        (micropub.artifact_id, claim_id, seq)
                    )
                )

    return (
        MicropublicationSidecarRows(
            micropublication_rows=tuple(micropublication_rows),
            claim_rows=tuple(claim_rows),
        ),
        tuple(diagnostics),
    )


def compile_sidecar_build_plan(
    repository_checked_bundle: RepositoryCheckedBundle,
    *,
    source_entries: Iterable[tuple[str, SourceDocument]],
    stance_entries: Iterable[tuple[str, StanceFileDocument]],
    justification_entries: Iterable[tuple[str, SourceJustificationsDocument]],
    micropub_files: Iterable[tuple[str, MicropublicationsFileDocument]],
) -> SidecarBuildPlan:
    claim_rows: ClaimSidecarRows | None = None
    raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(())
    conflict_rows: tuple[ConflictWitnessInsertRow, ...] = ()
    claim_fts_rows: tuple[ClaimFtsInsertRow, ...] = ()
    stance_rows: tuple[ClaimStanceInsertRow, ...] = ()
    justification_rows: tuple[JustificationInsertRow, ...] = ()
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...] = ()
    claim_reference_map: dict[str, str] = {}

    if repository_checked_bundle.normalized_claim_files is not None:
        checked_claims = repository_checked_bundle.claim_checked_bundle
        if checked_claims is None:
            raise ValueError("checked claim bundle is required to populate claims")
        normalized_claim_files = repository_checked_bundle.normalized_claim_files
        claim_reference_map = compile_claim_reference_map(normalized_claim_files)
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
        claim_fts_rows = compile_claim_fts_rows(normalized_claim_files)
        stance_rows, stance_quarantine_diagnostics = (
            _compile_authored_stance_sidecar_rows_with_diagnostics(
                stance_entries,
                claim_reference_map,
            )
        )
        justification_rows, justification_quarantine_diagnostics = (
            _compile_authored_justification_sidecar_rows_with_diagnostics(
                justification_entries,
                claim_reference_map,
            )
        )
        quarantine_diagnostics = (
            quarantine_diagnostics
            + stance_quarantine_diagnostics
            + justification_quarantine_diagnostics
        )

    micropublication_rows, micropublication_quarantine_diagnostics = (
        _compile_micropublication_sidecar_rows_with_diagnostics(
            micropub_files,
            claim_reference_map,
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
        ),
        context_rows=compile_context_sidecar_rows(
            repository_checked_bundle.context_files,
        ),
        claim_rows=claim_rows,
        raw_id_quarantine_rows=raw_id_quarantine_rows,
        conflict_rows=conflict_rows,
        claim_fts_rows=claim_fts_rows,
        micropublication_rows=micropublication_rows,
        stance_rows=stance_rows,
        justification_rows=justification_rows,
        quarantine_diagnostics=quarantine_diagnostics,
    )

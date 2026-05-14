"""Sidecar row compilation passes."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Sequence

from ast_equiv import canonical_dump
from ast_equiv.canonicalizer import AlgorithmParseError
from quire.references import FamilyReferenceIndex

from propstore.claims import (
    ClaimFileEntry,
    claim_file_claims,
    claim_file_filename,
    claim_file_stage,
)
from propstore.context_lifting import IstProposition, LiftedAssertion, LiftingDecision
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
from propstore.families.contexts.stages import (
    LoadedContext,
    coerce_loaded_contexts,
    loaded_contexts_to_lifting_system,
)
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.documents.sources import SourceDocument
from propstore.families.claims.stages import RawIdQuarantineRecord
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.documents.stances import StanceDocument
from propstore.families.forms.stages import (
    FormDefinition,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups
from propstore.propagation import rewrite_parameterization_symbols
from propstore.sidecar.claim_utils import (
    extract_deferred_stance_rows_with_diagnostics,
    prepare_claim_insert_row,
    prepare_claim_concept_link_rows,
)
from propstore.sidecar.stages import (
    ClaimSidecarRows,
    ContextSidecarRows,
    ConceptRelationshipProjectionRow,
    ConceptSidecarRows,
    MicropublicationSidecarRows,
    RawIdQuarantineSidecarRows,
    QuarantineDiagnostic,
    RepositoryCheckedBundle,
    SidecarBuildPlan,
)
from propstore.sidecar.claims import (
    ClaimAlgorithmPayloadProjectionRow,
    ClaimConceptLinkProjectionRow,
    ClaimCoreProjectionRow,
    ClaimFtsProjectionRow,
    ClaimNumericPayloadProjectionRow,
    ClaimStanceProjectionRow,
    ClaimTextPayloadProjectionRow,
    ConflictWitnessProjectionRow,
    JustificationProjectionRow,
)
from propstore.sidecar.contexts import (
    ContextAssumptionProjectionRow,
    ContextLiftingMaterializationProjectionRow,
    ContextLiftingRuleProjectionRow,
    ContextProjectionRow,
)
from propstore.sidecar.diagnostics import BuildDiagnosticProjectionRow
from propstore.sidecar.micropublications import (
    MicropublicationClaimProjectionRow,
    MicropublicationProjectionRow,
)
from propstore.sidecar.relations import RelationEdgeProjectionRow
from propstore.sidecar.concepts import (
    AliasProjectionRow,
    ConceptFtsProjectionRow,
    ConceptProjectionRow,
    FormAlgebraProjectionRow,
    FormProjectionRow,
    ParameterizationGroupProjectionRow,
    ParameterizationProjectionRow,
)
from propstore.sidecar.sources import SourceProjectionRow
from propstore.sidecar.claim_utils import (
    coerce_stance_resolution,
    resolution_opinion_columns,
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
) -> tuple[SourceProjectionRow, ...]:
    rows: list[SourceProjectionRow] = []
    for slug, source_doc in sources:
        origin = source_doc.origin
        trust = source_doc.trust
        rows.append(
            SourceProjectionRow(
                slug=slug,
                source_id=str(source_doc.id or slug),
                kind=source_doc.kind.value,
                origin_type=origin.type.value,
                origin_value=origin.value,
                origin_retrieved=origin.retrieved,
                origin_content_ref=origin.content_ref,
                prior_base_rate=_opinion_json(trust.prior_base_rate),
                quality_json=None
                if trust.quality is None
                else json.dumps(trust.quality.to_payload()),
                derived_from_json=None
                if not trust.derived_from
                else json.dumps(list(trust.derived_from)),
                artifact_code=source_doc.artifact_code,
            )
        )
    return tuple(rows)


def compile_context_sidecar_rows(
    contexts: Sequence[LoadedContext],
    *,
    authored_ist_assertions: Sequence[IstProposition] = (),
) -> ContextSidecarRows:
    context_rows: list[ContextProjectionRow] = []
    assumption_rows: list[ContextAssumptionProjectionRow] = []
    lifting_rule_rows: list[ContextLiftingRuleProjectionRow] = []

    for context in coerce_loaded_contexts(contexts):
        record = context.record
        if record.context_id is None:
            continue
        context_id = str(record.context_id)

        context_rows.append(
            ContextProjectionRow(
                id=context_id,
                name=record.name or "",
                description=record.description,
                parameters_json=json.dumps(dict(record.parameters), sort_keys=True)
                if record.parameters
                else None,
                perspective=record.perspective,
            )
        )

        for seq, assumption in enumerate(record.assumptions, 1):
            assumption_rows.append(
                ContextAssumptionProjectionRow(
                    context_id=context_id,
                    assumption_cel=assumption,
                    seq=seq,
                )
            )

        for rule in record.lifting_rules:
            lifting_rule_rows.append(
                ContextLiftingRuleProjectionRow(
                    id=rule.id,
                    source_context_id=str(rule.source.id),
                    target_context_id=str(rule.target.id),
                    conditions_cel=json.dumps(list(rule.conditions), sort_keys=True)
                    if rule.conditions
                    else None,
                    mode=rule.mode.value,
                    justification=rule.justification,
                )
            )

    materialization_rows = ()
    if authored_ist_assertions:
        lifting_system = loaded_contexts_to_lifting_system(contexts)
        decisions = tuple(
            decision
            for assertion in authored_ist_assertions
            for decision in lifting_system.lift_decisions_for(assertion)
        )
        materialization_rows = compile_context_lifting_materialization_rows(
            decisions
        )

    return ContextSidecarRows(
        context_rows=tuple(context_rows),
        assumption_rows=tuple(assumption_rows),
        lifting_rule_rows=tuple(lifting_rule_rows),
        lifting_materialization_rows=materialization_rows,
    )


def compile_context_lifting_materialization_rows(
    materializations: Sequence[LiftedAssertion | LiftingDecision],
) -> tuple[ContextLiftingMaterializationProjectionRow, ...]:
    rows: list[ContextLiftingMaterializationProjectionRow] = []
    for materialization in materializations:
        if isinstance(materialization, LiftingDecision):
            provenance = materialization.provenance.to_payload()
            exception_id = materialization.provenance.exception_id
            rows.append(
                ContextLiftingMaterializationProjectionRow(
                    rule_id=materialization.rule_id,
                    source_context_id=str(materialization.source_context.id),
                    target_context_id=str(materialization.target_context.id),
                    proposition_id=materialization.proposition_id,
                    status=materialization.status.value,
                    exception_id=exception_id,
                    provenance_json=json.dumps(provenance, sort_keys=True),
                )
            )
            continue
        rows.append(
            ContextLiftingMaterializationProjectionRow(
                rule_id=materialization.rule_id,
                source_context_id=str(materialization.source_context.id),
                target_context_id=str(materialization.target_context.id),
                proposition_id=materialization.proposition_id,
                status=materialization.status.value,
                exception_id=materialization.exception_id,
                provenance_json=json.dumps(materialization.provenance, sort_keys=True),
            )
        )
    return tuple(rows)


def compile_concept_sidecar_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptSidecarRows:
    form_rows: list[FormProjectionRow] = []
    concept_rows: list[ConceptProjectionRow] = []
    alias_rows: list[AliasProjectionRow] = []
    relationship_rows: list[ConceptRelationshipProjectionRow] = []
    relation_edge_rows: list[RelationEdgeProjectionRow] = []
    parameterization_rows: list[ParameterizationProjectionRow] = []
    parameterization_group_rows: list[ParameterizationGroupProjectionRow] = []
    form_algebra_rows: list[FormAlgebraProjectionRow] = []
    concept_fts_rows: list[ConceptFtsProjectionRow] = []

    for form_definition in form_registry.values():
        dimensions_json = (
            json.dumps(form_definition.dimensions)
            if form_definition.dimensions is not None
            else None
        )
        form_rows.append(
            FormProjectionRow(
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
            ConceptProjectionRow(
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
                AliasProjectionRow(
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
                RelationEdgeProjectionRow(
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
                ParameterizationProjectionRow(
                    output_concept_id=concept_id,
                    concept_ids=json.dumps(inputs),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=str(parameterization.exactness),
                    conditions_cel=conditions_json,
                    conditions_ir=conditions_ir,
                )
            )

        alias_names = [alias.name for alias in record.aliases]
        conditions_parts: list[str] = []
        for relationship in record.relationships:
            conditions_parts.extend(relationship.conditions)
        for parameterization in record.parameterizations:
            conditions_parts.extend(parameterization.conditions)
        concept_fts_rows.append(
            ConceptFtsProjectionRow(
                concept_id=concept_id,
                canonical_name=record.canonical_name,
                aliases=" ".join(alias_names),
                definition=record.definition,
                conditions=" ".join(conditions_parts),
            )
        )

    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            parameterization_group_rows.append(
                ParameterizationGroupProjectionRow(
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
        concept_fts_rows=tuple(concept_fts_rows),
    )


def _compile_form_algebra_rows(
    concepts: list[LoadedConcept],
    form_registry: dict[str, FormDefinition],
) -> tuple[FormAlgebraProjectionRow, ...]:
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
    rows: list[FormAlgebraProjectionRow] = []

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
                FormAlgebraProjectionRow(
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
    claim_core_rows: list[ClaimCoreProjectionRow] = []
    numeric_payload_rows: list[ClaimNumericPayloadProjectionRow] = []
    text_payload_rows: list[ClaimTextPayloadProjectionRow] = []
    algorithm_payload_rows: list[ClaimAlgorithmPayloadProjectionRow] = []
    claim_link_rows: list[ClaimConceptLinkProjectionRow] = []
    stance_rows: list[ClaimStanceProjectionRow] = []
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
            claim_core_rows.append(ClaimCoreProjectionRow.from_claim_mapping(row))
            numeric_payload_rows.append(
                ClaimNumericPayloadProjectionRow.from_claim_mapping(row)
            )
            text_payload_rows.append(
                ClaimTextPayloadProjectionRow.from_claim_mapping(row)
            )
            algorithm_payload_rows.append(
                ClaimAlgorithmPayloadProjectionRow.from_claim_mapping(row)
            )
            claim_link_rows.extend(
                ClaimConceptLinkProjectionRow.from_values(values)
                for values in prepare_claim_concept_link_rows(semantic_claim)
            )
            deferred_stance_rows, deferred_stance_diagnostics = (
                extract_deferred_stance_rows_with_diagnostics(
                    semantic_claim,
                    claim_index,
                )
            )
            stance_rows.extend(
                ClaimStanceProjectionRow.from_values(values)
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


def compile_authored_stance_sidecar_rows(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[ClaimStanceProjectionRow, ...]:
    rows, diagnostics = _compile_authored_stance_sidecar_rows_with_diagnostics(
        stance_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_authored_stance_sidecar_rows_with_diagnostics(
    stance_entries: Iterable[tuple[str, StanceDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[ClaimStanceProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[ClaimStanceProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, stance in stance_entries:
        source_claim = claim_index.resolve_id(stance.source_claim)
        if source_claim is None or source_claim not in valid_claims:
            missing_source = stance.source_claim or filename
            message = (
                f"stance artifact {filename} references nonexistent source claim "
                f"'{missing_source}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_source,
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        stance_payload = stance.to_payload()
        target = claim_index.resolve_id(stance.target or "")
        stance_type = stance_payload.get("type") or ""
        if target is None or target not in valid_claims:
            missing_target = stance.target or filename
            message = (
                f"stance artifact {filename} references nonexistent target claim "
                f"'{missing_target}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_target,
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        if stance_type not in VALID_STANCE_TYPES:
            raise ValueError(
                f"stance artifact {filename} uses unrecognized stance type "
                f"'{stance_type}'"
            )

        resolution = coerce_stance_resolution(
            stance_payload.get("resolution"),
            f"stance artifact {filename}",
        )
        opinion_columns = resolution_opinion_columns(resolution)
        perspective_source_claim = (
            claim_index.resolve_id(
                stance.perspective_source_claim_id or stance.source_claim
            )
            or source_claim
        )
        rows.append(
            ClaimStanceProjectionRow.from_values(
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
                    perspective_source_claim,
                )
            )
        )
    return tuple(rows), tuple(diagnostics)


def compile_authored_justification_sidecar_rows(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[JustificationProjectionRow, ...]:
    rows, diagnostics = _compile_authored_justification_sidecar_rows_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_authored_justification_sidecar_rows_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[JustificationProjectionRow, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    rows: list[JustificationProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification.to_payload()
        justification_id = justification.id
        conclusion = claim_index.resolve_id(justification.conclusion)
        if not isinstance(justification_id, str) or not justification_id:
            raise ValueError(
                f"justification artifact {filename} missing id"
            )
        if not isinstance(conclusion, str) or conclusion not in valid_claims:
            message = (
                f"justification artifact {filename} references "
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
            resolved_premise = claim_index.resolve_id(premise)
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
                f"justification artifact {filename} references "
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
            JustificationProjectionRow.from_values(
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
) -> tuple[ConflictWitnessProjectionRow, ...]:
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
        ConflictWitnessProjectionRow.from_values(
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
) -> tuple[ClaimFtsProjectionRow, ...]:
    rows: list[ClaimFtsProjectionRow] = []
    for claim_file in claim_files:
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id
            if not isinstance(claim_id, str) or not claim_id:
                continue
            rows.append(
                ClaimFtsProjectionRow.from_values(
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
    claim_rows: list[ClaimCoreProjectionRow] = []
    diagnostic_rows: list[BuildDiagnosticProjectionRow] = []

    for record in records:
        claim_rows.append(
            ClaimCoreProjectionRow.from_claim_mapping(
                {
                    "id": record.synthetic_id,
                    "primary_logical_id": "",
                    "logical_ids_json": "[]",
                    "version_id": "",
                    "content_hash": "",
                    "seq": record.seq,
                    "type": "quarantine",
                    "target_concept": None,
                    "source_slug": record.source_paper,
                    "source_paper": record.source_paper,
                    "provenance_page": 0,
                    "provenance_json": None,
                    "context_id": None,
                    "premise_kind": "ordinary",
                    "branch": None,
                    "build_status": "blocked",
                    "stage": None,
                    "promotion_status": None,
                }
            )
        )
        diagnostic_rows.append(
            BuildDiagnosticProjectionRow.from_values(
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
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> MicropublicationSidecarRows:
    rows, diagnostics = _compile_micropublication_sidecar_rows_with_diagnostics(
        micropub_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return rows


def _compile_micropublication_sidecar_rows_with_diagnostics(
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[MicropublicationSidecarRows, tuple[QuarantineDiagnostic, ...]]:
    valid_claim_ids = set(claim_index.ids())
    micropublication_rows: list[MicropublicationProjectionRow] = []
    claim_rows: list[MicropublicationClaimProjectionRow] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, micropub in sorted(micropub_entries, key=lambda item: item[0]):
        resolved_claims: list[str] = []
        missing_claim_ref: str | None = None
        for claim_id in micropub.claims:
            resolved_claim = claim_index.resolve_id(claim_id)
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
                f"micropublication artifact {micropub.artifact_id} references "
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
            MicropublicationProjectionRow(
                id=micropub.artifact_id,
                context_id=str(micropub.context.id),
                assumptions_json=json.dumps(
                    list(micropub.assumptions),
                    sort_keys=True,
                ),
                evidence_json=json.dumps(
                    [item.to_payload() for item in micropub.evidence],
                    sort_keys=True,
                ),
                stance=None if micropub.stance is None else micropub.stance.value,
                provenance_json=(
                    None
                    if micropub.provenance is None
                    else json.dumps(
                        micropub.provenance.to_payload(),
                        sort_keys=True,
                    )
                ),
                source_slug=micropub.source,
            )
        )
        for seq, claim_id in enumerate(resolved_claims, start=1):
            assert claim_id is not None
            claim_rows.append(
                MicropublicationClaimProjectionRow(
                    micropublication_id=micropub.artifact_id,
                    claim_id=claim_id,
                    seq=seq,
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
    stance_entries: Iterable[tuple[str, StanceDocument]],
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
) -> SidecarBuildPlan:
    claim_rows: ClaimSidecarRows | None = None
    raw_id_quarantine_rows = compile_raw_id_quarantine_sidecar_rows(())
    conflict_rows: tuple[ConflictWitnessProjectionRow, ...] = ()
    claim_fts_rows: tuple[ClaimFtsProjectionRow, ...] = ()
    stance_rows: tuple[ClaimStanceProjectionRow, ...] = ()
    justification_rows: tuple[JustificationProjectionRow, ...] = ()
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
        claim_fts_rows = compile_claim_fts_rows(normalized_claim_files)
        stance_rows, stance_quarantine_diagnostics = (
            _compile_authored_stance_sidecar_rows_with_diagnostics(
                stance_entries,
                claim_index,
            )
        )
        justification_rows, justification_quarantine_diagnostics = (
            _compile_authored_justification_sidecar_rows_with_diagnostics(
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
        _compile_micropublication_sidecar_rows_with_diagnostics(
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
        claim_fts_rows=claim_fts_rows,
        micropublication_rows=micropublication_rows,
        stance_rows=stance_rows,
        justification_rows=justification_rows,
        quarantine_diagnostics=quarantine_diagnostics,
    )

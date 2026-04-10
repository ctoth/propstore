"""Claim compiler passes."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any, Mapping

import jsonschema

from propstore.claim_documents import ClaimDocument, LoadedClaimFile
from propstore.cel_checker import check_cel_expression
from propstore.compiler.context import (
    CompilationContext,
    _build_claim_lookup,
    concept_registry_for_context,
)
from propstore.diagnostics import SemanticDiagnostic, ValidationResult
from propstore.compiler.ir import (
    ClaimCompilationBundle,
    ResolvedReference,
    SemanticClaim,
    SemanticClaimFile,
    SemanticStance,
)
from propstore.identity import (
    CLAIM_ARTIFACT_ID_RE,
    CLAIM_VERSION_ID_RE,
    compute_claim_version_id,
)


def _diagnostics_from_validation_result(
    result: ValidationResult,
) -> list[SemanticDiagnostic]:
    diagnostics: list[SemanticDiagnostic] = []
    diagnostics.extend(
        SemanticDiagnostic(level="error", message=message)
        for message in result.errors
    )
    diagnostics.extend(
        SemanticDiagnostic(level="warning", message=message)
        for message in result.warnings
    )
    return diagnostics


def _concept_match_kind(
    raw_text: str,
    resolved_id: str,
    context: CompilationContext,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    concept = context.concepts_by_id.get(resolved_id)
    if concept is None:
        return None, None
    if concept.canonical_name == raw_text:
        return "canonical_name", raw_text
    for logical_id in concept.logical_ids:
        if logical_id.formatted == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    for alias in concept.aliases:
        if alias.name == raw_text:
            return "alias", raw_text
    if raw_text in context.concept_lookup:
        return "legacy_key", raw_text
    return None, None


def _resolve_concept_reference(
    concept_ref: object,
    context: CompilationContext,
) -> ResolvedReference | None:
    if not isinstance(concept_ref, str) or not concept_ref:
        return None
    candidates = context.concept_lookup.get(concept_ref, ())
    if len(candidates) == 1:
        matched_by, matched_text = _concept_match_kind(concept_ref, candidates[0], context)
        return ResolvedReference(
            raw_text=concept_ref,
            target_kind="concept",
            resolved_id=candidates[0],
            matched_by=matched_by,
            matched_text=matched_text,
        )
    return ResolvedReference(
        raw_text=concept_ref,
        target_kind="concept",
        resolved_id=None,
        matched_by=None,
        matched_text=None,
        ambiguous_candidates=tuple(candidates),
    )


def _claim_match_kind(
    raw_text: str,
    resolved_id: str,
    normalized_claim_files: list[LoadedClaimFile],
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    for claim_file in normalized_claim_files:
        for claim in claim_file.claims:
            if claim.artifact_id != resolved_id:
                continue
            for logical_id in claim.logical_ids:
                if logical_id.formatted == raw_text:
                    return "logical_id", raw_text
                if logical_id.value == raw_text:
                    return "logical_value", raw_text
            break
    return None, None


def _resolve_claim_reference(
    claim_ref: object,
    claim_lookup: Mapping[str, tuple[str, ...]],
    normalized_claim_files: list[LoadedClaimFile],
) -> ResolvedReference | None:
    if not isinstance(claim_ref, str) or not claim_ref:
        return None
    candidates = claim_lookup.get(claim_ref, ())
    if len(candidates) == 1:
        matched_by, matched_text = _claim_match_kind(claim_ref, candidates[0], normalized_claim_files)
        return ResolvedReference(
            raw_text=claim_ref,
            target_kind="claim",
            resolved_id=candidates[0],
            matched_by=matched_by,
            matched_text=matched_text,
        )
    return ResolvedReference(
        raw_text=claim_ref,
        target_kind="claim",
        resolved_id=None,
        matched_by=None,
        matched_text=None,
        ambiguous_candidates=tuple(candidates),
    )


def _bind_claim(
    claim: ClaimDocument,
    *,
    filename: str,
    source_paper: str,
    context: CompilationContext,
    claim_lookup: Mapping[str, tuple[str, ...]],
    normalized_claim_files: list[LoadedClaimFile],
) -> SemanticClaim:
    authored_claim = claim.to_payload()
    resolved_claim = copy.deepcopy(authored_claim)

    concept_ref = _resolve_concept_reference(claim.concept, context)
    if concept_ref is not None and concept_ref.resolved_id is not None:
        resolved_claim["concept"] = concept_ref.resolved_id

    target_concept_ref = _resolve_concept_reference(claim.target_concept, context)
    if target_concept_ref is not None and target_concept_ref.resolved_id is not None:
        resolved_claim["target_concept"] = target_concept_ref.resolved_id

    concept_refs: list[ResolvedReference] = []
    if claim.concepts:
        rewritten_concepts: list[object] = []
        for concept_value in claim.concepts:
            concept_binding = _resolve_concept_reference(concept_value, context)
            if concept_binding is not None:
                concept_refs.append(concept_binding)
                rewritten_concepts.append(concept_binding.resolved_id or concept_binding.raw_text)
            else:
                rewritten_concepts.append(concept_value)
        resolved_claim["concepts"] = rewritten_concepts

    variable_refs: list[ResolvedReference] = []
    if claim.variables:
        if isinstance(claim.variables, dict):
            rewritten_variables: dict[str, object] = {}
            for variable_name, concept_value in claim.variables.items():
                binding = _resolve_concept_reference(concept_value, context)
                if binding is not None:
                    variable_refs.append(binding)
                    rewritten_variables[variable_name] = (
                        binding.resolved_id or binding.raw_text
                    )
                else:
                    rewritten_variables[variable_name] = concept_value
            resolved_claim["variables"] = rewritten_variables
        else:
            rewritten_variables_list: list[object] = []
            for variable in claim.variables:
                updated = variable.to_payload()
                binding = _resolve_concept_reference(variable.concept, context)
                if binding is not None:
                    variable_refs.append(binding)
                    updated["concept"] = binding.resolved_id or binding.raw_text
                rewritten_variables_list.append(updated)
            resolved_claim["variables"] = rewritten_variables_list

    parameter_refs: list[ResolvedReference] = []
    if claim.parameters:
        rewritten_parameters: list[object] = []
        for parameter in claim.parameters:
            updated = parameter.to_payload()
            binding = _resolve_concept_reference(parameter.concept, context)
            if binding is not None:
                parameter_refs.append(binding)
                updated["concept"] = binding.resolved_id or binding.raw_text
            rewritten_parameters.append(updated)
        resolved_claim["parameters"] = rewritten_parameters

    semantic_stances: list[SemanticStance] = []
    if claim.stances:
        rewritten_stances: list[object] = []
        for stance in claim.stances:
            updated = stance.to_payload()
            target_ref = _resolve_claim_reference(
                stance.target,
                claim_lookup,
                normalized_claim_files,
            )
            if target_ref is None:
                rewritten_stances.append(updated)
                continue
            updated["target"] = target_ref.resolved_id or target_ref.raw_text
            semantic_stances.append(SemanticStance(data=updated, target_ref=target_ref))
            rewritten_stances.append(updated)
        resolved_claim["stances"] = rewritten_stances

    return SemanticClaim(
        filename=filename,
        source_paper=source_paper,
        artifact_id=claim.artifact_id if isinstance(claim.artifact_id, str) else None,
        claim_type=claim.type if isinstance(claim.type, str) else None,
        authored_claim=authored_claim,
        resolved_claim=resolved_claim,
        concept_ref=concept_ref,
        target_concept_ref=target_concept_ref,
        concept_refs=tuple(concept_refs),
        variable_refs=tuple(variable_refs),
        parameter_refs=tuple(parameter_refs),
        stances=tuple(semantic_stances),
    )


def compile_claim_files(
    claim_files: list[LoadedClaimFile],
    context: CompilationContext,
    *,
    context_ids: set[str] | None = None,
) -> ClaimCompilationBundle:
    """Run normalization, binding, and semantic validation over claim files."""
    from propstore.validate_claims import (
        _coerce_schema_numeric_strings,
        _load_claim_schema,
        _validate_algorithm,
        _validate_equation,
        _validate_logical_ids,
        _validate_measurement,
        _validate_model,
        _validate_observation,
        _validate_parameter,
        _validate_stances,
    )
    from propstore.form_utils import json_safe

    normalized_claim_files = list(claim_files)
    claim_lookup = _build_claim_lookup(normalized_claim_files)
    effective_context = replace(context, claim_lookup=claim_lookup)
    concept_registry = concept_registry_for_context(effective_context)

    diagnostics: list[SemanticDiagnostic] = []
    semantic_files: list[SemanticClaimFile] = []
    seen_artifact_ids: dict[str, str] = {}
    seen_logical_ids: dict[str, str] = {}
    all_artifact_ids: set[str] = set()
    for claim_file in normalized_claim_files:
        for claim in claim_file.claims:
            artifact_id = claim.artifact_id
            if isinstance(artifact_id, str) and artifact_id:
                all_artifact_ids.add(artifact_id)

    json_schema = _load_claim_schema()

    for original_file, normalized_file in zip(claim_files, normalized_claim_files, strict=False):
        file_diagnostics: list[SemanticDiagnostic] = []
        semantic_claims: list[SemanticClaim] = []
        data = normalized_file.data

        if normalized_file.stage == "draft":
            file_diagnostics.append(
                SemanticDiagnostic(
                    level="error",
                    filename=normalized_file.filename,
                    message=(
                        "draft artifacts are not accepted in the final claim validation path"
                    ),
                )
            )
            diagnostics.extend(file_diagnostics)
            semantic_files.append(
                SemanticClaimFile(
                    loaded_entry=original_file,
                    normalized_entry=normalized_file,
                    claims=tuple(),
                )
            )
            continue

        try:
            jsonschema.validate(
                _coerce_schema_numeric_strings(json_safe(data)),
                json_schema,
            )
        except jsonschema.ValidationError as exc:
            file_diagnostics.append(
                SemanticDiagnostic(
                    level="error",
                    message=f"{normalized_file.filename}: JSON Schema error: {exc.message}",
                )
            )

        source_paper = normalized_file.source_paper

        for claim in normalized_file.claims:
            raw_id = claim.id
            artifact_id = claim.artifact_id
            if isinstance(raw_id, str) and raw_id and not artifact_id:
                file_diagnostics.append(
                    SemanticDiagnostic(
                        level="error",
                        message=(
                            f"{normalized_file.filename}: claim uses raw 'id' input "
                            "without canonical identity fields"
                        ),
                    )
                )
                continue

            semantic_claim = _bind_claim(
                claim,
                filename=normalized_file.filename,
                source_paper=source_paper,
                context=effective_context,
                claim_lookup=claim_lookup,
                normalized_claim_files=normalized_claim_files,
            )
            semantic_claims.append(semantic_claim)

            per_claim = ValidationResult()
            cid = semantic_claim.resolved_claim.get("artifact_id")
            ctype = semantic_claim.resolved_claim.get("type")

            if not cid:
                per_claim.errors.append(f"{normalized_file.filename}: claim missing 'artifact_id'")
                file_diagnostics.extend(_diagnostics_from_validation_result(per_claim))
                continue

            if cid in seen_artifact_ids:
                per_claim.errors.append(
                    f"{normalized_file.filename}: duplicate claim artifact_id '{cid}' "
                    f"(also in {seen_artifact_ids[cid]})"
                )
            else:
                seen_artifact_ids[cid] = normalized_file.filename

            if "id" in semantic_claim.resolved_claim:
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim '{cid}' uses raw 'id' input; "
                    "use artifact_id and logical_ids"
                )

            if not CLAIM_ARTIFACT_ID_RE.match(cid):
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim artifact_id '{cid}' does not match "
                    "required format ps:claim:<opaque-token>"
                )

            _validate_logical_ids(
                semantic_claim.resolved_claim.get("logical_ids"),
                filename=normalized_file.filename,
                artifact_id=cid,
                seen_logical_ids=seen_logical_ids,
                result=per_claim,
            )

            version_id = semantic_claim.resolved_claim.get("version_id")
            if not isinstance(version_id, str) or not CLAIM_VERSION_ID_RE.match(version_id):
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim '{cid}' version_id must match "
                    "sha256:<64 hex chars>"
                )
            else:
                expected_version_id = compute_claim_version_id(semantic_claim.authored_claim)
                if version_id != expected_version_id:
                    per_claim.errors.append(
                        f"{normalized_file.filename}: claim '{cid}' version_id mismatch "
                        f"(expected {expected_version_id})"
                    )

            provenance = semantic_claim.resolved_claim.get("provenance")
            if not provenance or not isinstance(provenance, dict):
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim '{cid}' missing provenance"
                )
            else:
                if not provenance.get("paper"):
                    per_claim.errors.append(
                        f"{normalized_file.filename}: claim '{cid}' provenance missing 'paper'"
                    )
                if provenance.get("page") is None:
                    per_claim.errors.append(
                        f"{normalized_file.filename}: claim '{cid}' provenance missing 'page'"
                    )

            claim_context = semantic_claim.resolved_claim.get("context")
            if claim_context and context_ids is not None and claim_context not in context_ids:
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim '{cid}' references nonexistent "
                    f"context '{claim_context}'"
                )

            conditions = semantic_claim.resolved_claim.get("conditions")
            if conditions and isinstance(conditions, list):
                for cel_expr in conditions:
                    if not isinstance(cel_expr, str):
                        continue
                    cel_errors = check_cel_expression(
                        cel_expr,
                        dict(effective_context.cel_registry),
                    )
                    for error in cel_errors:
                        if error.is_warning:
                            per_claim.warnings.append(
                                f"{normalized_file.filename}: claim '{cid}' CEL warning: "
                                f"{error.message}"
                            )
                        else:
                            per_claim.errors.append(
                                f"{normalized_file.filename}: claim '{cid}' CEL error: "
                                f"{error.message}"
                            )

            if ctype == "parameter":
                _validate_parameter(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype == "equation":
                _validate_equation(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype == "observation":
                _validate_observation(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype == "model":
                _validate_model(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype == "measurement":
                _validate_measurement(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype == "algorithm":
                _validate_algorithm(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                )
            elif ctype in ("mechanism", "comparison", "limitation"):
                _validate_observation(
                    semantic_claim.resolved_claim,
                    cid,
                    normalized_file.filename,
                    concept_registry,
                    per_claim,
                    claim_type=ctype,
                )
            else:
                per_claim.errors.append(
                    f"{normalized_file.filename}: claim '{cid}' has unrecognized type '{ctype}'"
                )

            _validate_stances(
                semantic_claim.resolved_claim,
                cid,
                normalized_file.filename,
                all_artifact_ids,
                per_claim,
            )
            file_diagnostics.extend(_diagnostics_from_validation_result(per_claim))

        diagnostics.extend(file_diagnostics)
        semantic_files.append(
            SemanticClaimFile(
                loaded_entry=original_file,
                normalized_entry=normalized_file,
                claims=tuple(semantic_claims),
            )
        )

    return ClaimCompilationBundle(
        context=effective_context,
        normalized_claim_files=tuple(normalized_claim_files),
        semantic_files=tuple(semantic_files),
        diagnostics=tuple(diagnostics),
    )

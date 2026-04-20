"""Claim compiler passes."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from propstore.families.claims.documents import ClaimDocument
from propstore.cel_checker import check_cel_expr
from propstore.cel_types import CheckedCelExpr, checked_condition_set
from quire.documents import convert_document_value
from propstore.claims import (
    ClaimFileEntry,
    claim_file_claims,
    claim_file_filename,
    claim_file_source_paper,
    claim_file_stage,
    load_claim_file,
)
from propstore.families.claims.passes.checks import (
    _validate_logical_ids,
    _validate_stances,
    validate_claim_semantics,
)
from propstore.compiler.context import (
    CompilationContext,
    _build_claim_lookup,
)
from propstore.compiler.references import (
    resolve_claim_reference,
    resolve_concept_reference,
)
from propstore.diagnostics import SemanticDiagnostic, ValidationResult
from propstore.compiler.ir import (
    ClaimCompilationBundle,
    ResolvedReference,
    SemanticClaim,
    SemanticClaimFile,
    SemanticStance,
)
from propstore.families.identity.logical_ids import (
    CLAIM_ARTIFACT_ID_RE,
    CLAIM_VERSION_ID_RE,
)
from propstore.families.claims.stages import (
    ClaimAuthoredFiles,
    ClaimCheckedBundle,
    ClaimStage,
    RawIdQuarantineRecord,
)
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult
from propstore.families.identity.claims import compute_claim_version_id


def _bind_claim(
    claim: ClaimDocument,
    *,
    filename: str,
    source_paper: str,
    context: CompilationContext,
    normalized_claim_files: Sequence[ClaimFileEntry],
) -> SemanticClaim:
    authored_claim = claim.to_payload()
    resolved_claim = copy.deepcopy(authored_claim)

    concept_ref = resolve_concept_reference(claim.concept, context)
    if concept_ref is not None and concept_ref.resolved_id is not None:
        resolved_claim["concept"] = concept_ref.resolved_id

    target_concept_ref = resolve_concept_reference(claim.target_concept, context)
    if target_concept_ref is not None and target_concept_ref.resolved_id is not None:
        resolved_claim["target_concept"] = target_concept_ref.resolved_id

    concept_refs: list[ResolvedReference] = []
    if claim.concepts:
        rewritten_concepts: list[object] = []
        for concept_value in claim.concepts:
            concept_binding = resolve_concept_reference(concept_value, context)
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
                binding = resolve_concept_reference(concept_value, context)
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
                binding = resolve_concept_reference(variable.concept, context)
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
            binding = resolve_concept_reference(parameter.concept, context)
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
            target_ref = resolve_claim_reference(
                stance.target,
                context,
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
        resolved_claim=convert_document_value(
            resolved_claim,
            ClaimDocument,
            source=filename,
        ),
        concept_ref=concept_ref,
        target_concept_ref=target_concept_ref,
        concept_refs=tuple(concept_refs),
        variable_refs=tuple(variable_refs),
        parameter_refs=tuple(parameter_refs),
        stances=tuple(semantic_stances),
    )


def compile_claim_files(
    claim_files: Sequence[ClaimFileEntry],
    context: CompilationContext,
    *,
    context_ids: set[str] | None = None,
) -> ClaimCompilationBundle:
    """Run normalization, binding, and semantic validation over claim files."""
    normalized_claim_files = list(claim_files)
    claim_lookup = _build_claim_lookup(normalized_claim_files)
    effective_context = replace(context, claim_lookup=claim_lookup)

    diagnostics: list[SemanticDiagnostic] = []
    semantic_files: list[SemanticClaimFile] = []
    seen_artifact_ids: dict[str, str] = {}
    seen_logical_ids: dict[str, str] = {}
    all_artifact_ids: set[str] = set()
    for claim_file in normalized_claim_files:
        for claim in claim_file_claims(claim_file):
            artifact_id = claim.artifact_id
            if isinstance(artifact_id, str) and artifact_id:
                all_artifact_ids.add(artifact_id)

    for original_file, normalized_file in zip(claim_files, normalized_claim_files, strict=False):
        file_diagnostics: list[SemanticDiagnostic] = []
        semantic_claims: list[SemanticClaim] = []
        filename = claim_file_filename(normalized_file)
        source_paper = claim_file_source_paper(normalized_file)
        # Axis-1 finding 3.2 / ws-z-render-gates.md: draft files no longer
        # drop from the semantic bundle. They traverse the normal binding
        # path; the file-level draft marker rides through on
        # ``claim_core.stage='draft'`` and render-policy filtering (phase 4)
        # decides visibility. The informational diagnostic survives so
        # callers that want to flag drafts can still see them.
        if claim_file_stage(normalized_file) == "draft":
            file_diagnostics.append(
                SemanticDiagnostic(
                    level="info",
                    filename=filename,
                    message=(
                        "claim file is marked stage='draft'; "
                        "render policy hides drafts by default"
                    ),
                )
            )

        for claim in claim_file_claims(normalized_file):
            raw_id = claim.id
            artifact_id = claim.artifact_id
            if isinstance(raw_id, str) and raw_id and not artifact_id:
                file_diagnostics.append(
                    SemanticDiagnostic(
                        level="error",
                        message=(
                            "claim uses raw 'id' input "
                            "without canonical identity fields"
                        ),
                        filename=filename,
                    )
                )
                continue

            semantic_claim = _bind_claim(
                claim,
                filename=filename,
                source_paper=source_paper,
                context=effective_context,
                normalized_claim_files=normalized_claim_files,
            )
            semantic_claims.append(semantic_claim)
            resolved_claim = semantic_claim.resolved_claim.to_payload()

            cid = resolved_claim.get("artifact_id")

            if not cid:
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message="claim missing 'artifact_id'",
                    filename=filename,
                ))
                continue

            if cid in seen_artifact_ids:
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"duplicate claim artifact_id '{cid}' "
                        f"(also in {seen_artifact_ids[cid]})"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))
            else:
                seen_artifact_ids[cid] = filename

            if "id" in resolved_claim:
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' uses raw 'id' input; "
                        "use artifact_id and logical_ids"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))

            if not CLAIM_ARTIFACT_ID_RE.match(cid):
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim artifact_id '{cid}' does not match "
                        "required format ps:claim:<opaque-token>"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))

            _validate_logical_ids(
                resolved_claim.get("logical_ids"),
                filename=filename,
                artifact_id=cid,
                seen_logical_ids=seen_logical_ids,
                diagnostics=file_diagnostics,
            )

            version_id = resolved_claim.get("version_id")
            if not isinstance(version_id, str) or not CLAIM_VERSION_ID_RE.match(version_id):
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' version_id must match "
                        "sha256:<64 hex chars>"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))
            else:
                expected_version_id = compute_claim_version_id(semantic_claim.authored_claim)
                if version_id != expected_version_id:
                    file_diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=(
                            f"claim '{cid}' version_id mismatch "
                            f"(expected {expected_version_id})"
                        ),
                        filename=filename,
                        artifact_id=cid,
                    ))

            provenance = resolved_claim.get("provenance")
            if not provenance or not isinstance(provenance, dict):
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=f"claim '{cid}' missing provenance",
                    filename=filename,
                    artifact_id=cid,
                ))
            else:
                if not provenance.get("paper"):
                    file_diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=f"claim '{cid}' provenance missing 'paper'",
                        filename=filename,
                        artifact_id=cid,
                    ))
                if provenance.get("page") is None:
                    file_diagnostics.append(SemanticDiagnostic(
                        level="error",
                        message=f"claim '{cid}' provenance missing 'page'",
                        filename=filename,
                        artifact_id=cid,
                    ))

            raw_claim_context = resolved_claim.get("context")
            claim_context = (
                raw_claim_context.get("id")
                if isinstance(raw_claim_context, dict)
                else raw_claim_context
            )
            if not isinstance(claim_context, str) or not claim_context:
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=f"claim '{cid}' missing required context",
                    filename=filename,
                    artifact_id=cid,
                ))
            elif context_ids is not None and claim_context not in context_ids:
                file_diagnostics.append(SemanticDiagnostic(
                    level="error",
                    message=(
                        f"claim '{cid}' references nonexistent "
                        f"context '{claim_context}'"
                    ),
                    filename=filename,
                    artifact_id=cid,
                ))

            conditions = resolved_claim.get("conditions")
            if conditions and isinstance(conditions, list):
                checked_conditions: list[CheckedCelExpr] = []
                for cel_expr in conditions:
                    if not isinstance(cel_expr, str):
                        continue
                    try:
                        checked = check_cel_expr(cel_expr, effective_context.cel_registry)
                    except ValueError as exc:
                        file_diagnostics.append(SemanticDiagnostic(
                            level="error",
                            message=f"claim '{cid}' CEL error: {exc}",
                            filename=filename,
                            artifact_id=cid,
                        ))
                        continue
                    checked_conditions.append(checked)
                    for warning in checked.warnings:
                        file_diagnostics.append(SemanticDiagnostic(
                            level="warning",
                            message=(
                                f"claim '{cid}' CEL warning: "
                                f"{warning.message}"
                            ),
                            filename=filename,
                            artifact_id=cid,
                        ))
                if checked_conditions:
                    semantic_claim = replace(
                        semantic_claim,
                        checked_conditions=checked_condition_set(checked_conditions),
                    )
                    semantic_claims[-1] = semantic_claim

            validate_claim_semantics(
                resolved_claim,
                cid,
                filename,
                effective_context,
                file_diagnostics,
            )

            _validate_stances(
                resolved_claim,
                cid,
                filename,
                all_artifact_ids,
                file_diagnostics,
            )

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


def _synthesize_quarantine_id(filename: str, raw_id: str, seq: int) -> str:
    import hashlib

    digest = hashlib.sha256(f"{filename}|{raw_id}|{seq}".encode()).hexdigest()
    return f"quarantine:raw_id:{digest[:32]}"


def _collect_raw_id_quarantine_records(
    claim_bundle: ClaimCompilationBundle,
) -> tuple[RawIdQuarantineRecord, ...]:
    raw_id_filenames = {
        diagnostic.filename
        for diagnostic in claim_bundle.diagnostics
        if diagnostic.is_error and "raw 'id' input" in diagnostic.message
    }
    if not raw_id_filenames:
        return ()

    records: list[RawIdQuarantineRecord] = []
    seq = 0
    for claim_file in claim_bundle.normalized_claim_files:
        filename = claim_file_filename(claim_file)
        if filename not in raw_id_filenames:
            continue
        source_paper = claim_file_source_paper(claim_file) or filename
        for file_seq, claim in enumerate(claim_file_claims(claim_file), start=1):
            raw_id = claim.id
            artifact_id = claim.artifact_id
            if (
                isinstance(raw_id, str)
                and raw_id
                and not (isinstance(artifact_id, str) and artifact_id)
            ):
                seq += 1
                records.append(
                    RawIdQuarantineRecord(
                        filename=filename,
                        source_paper=str(source_paper),
                        raw_id=raw_id,
                        seq=seq,
                        synthetic_id=_synthesize_quarantine_id(
                            filename,
                            raw_id,
                            file_seq,
                        ),
                        message=(
                            "claim uses raw 'id' input "
                            "without canonical identity fields"
                        ),
                    )
                )
    return tuple(records)


def validate_claims(
    claim_files: Sequence[ClaimFileEntry],
    context: CompilationContext,
    context_ids: set[str] | None = None,
) -> ValidationResult:
    """Validate claim files against schema and compiler contract."""
    bundle = compile_claim_files(
        claim_files,
        context,
        context_ids=context_ids,
    )
    return bundle.to_validation_result()


def validate_single_claim_file(
    filepath: Path,
    context: CompilationContext,
) -> ValidationResult:
    """Validate a single typed claims YAML file."""
    loaded = load_claim_file(filepath)
    return validate_claims([loaded], context)


class ClaimCompilePass:
    family = PropstoreFamily.CLAIMS
    name = "claim.compile"
    input_stage = ClaimStage.AUTHORED
    output_stage = ClaimStage.CHECKED

    def run(
        self,
        value: ClaimAuthoredFiles,
        context: object,
    ) -> PassResult[ClaimCheckedBundle]:
        bundle = compile_claim_files(
            value.claim_files,
            value.context,
            context_ids=(
                None
                if value.context_ids is None
                else set(value.context_ids)
            ),
        )
        return PassResult(
            output=ClaimCheckedBundle(
                bundle=bundle,
                raw_id_quarantine_records=_collect_raw_id_quarantine_records(bundle),
            ),
            diagnostics=tuple(_pass_diagnostic(item) for item in bundle.diagnostics),
        )


def register_claim_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ClaimCompilePass, family=PropstoreFamily.CLAIMS)


def run_claim_pipeline(
    authored: ClaimAuthoredFiles,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    return run_pipeline(
        authored,
        family=PropstoreFamily.CLAIMS,
        start_stage=ClaimStage.AUTHORED,
        target_stage=ClaimStage.CHECKED,
        registry=registry,
        context=None,
    )


def _pass_diagnostic(diagnostic: SemanticDiagnostic) -> PassDiagnostic:
    return PassDiagnostic(
        level="error" if diagnostic.is_error else "warning",
        code=f"claim.{diagnostic.level}",
        message=diagnostic.message,
        family=PropstoreFamily.CLAIMS,
        stage=ClaimStage.CHECKED,
        filename=diagnostic.filename,
        artifact_id=diagnostic.artifact_id,
        pass_name="claim.compile",
    )

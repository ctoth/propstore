"""Claim compiler passes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import msgspec
from quire.documents import LoadedDocument, load_document

from propstore.families.claims.declaration import ClaimDocument
from propstore.families.claims.passes.checks import (
    _validate_logical_ids,
    _validate_stances,
    validate_claim_semantics,
)
from propstore.compiler.context import CompilationContext
from propstore.compiler.ir import ClaimCompilationBundle, SemanticClaim
from propstore.families.claims.stages import (
    ClaimCheckedBundle,
    ClaimStage,
    RawIdQuarantineRecord,
)
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult


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
    for loaded_claim in claim_bundle.claim_documents:
        claim = loaded_claim.document
        filename = loaded_claim.filename
        if filename not in raw_id_filenames:
            continue
        source = claim.source
        provenance = claim.provenance
        source_paper = (
            source.paper
            if source is not None
            else (
                provenance.paper
                if provenance is not None and provenance.paper is not None
                else filename
            )
        )
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
                        1,
                    ),
                    message=(
                        "claim uses raw 'id' input "
                        "without canonical identity fields"
                    ),
                )
            )
    return tuple(records)


def validate_claims(
    claim_files: Sequence[LoadedDocument[ClaimDocument]],
    context: CompilationContext,
    context_ids: set[str] | None = None,
) -> PipelineResult[object]:
    """Validate claim files against schema and compiler contract."""
    return run_claim_pipeline(claim_files, context, context_ids=context_ids)


def validate_single_claim_file(
    filepath: Path,
    context: CompilationContext,
) -> PipelineResult[object]:
    """Validate a single typed claims YAML file."""
    loaded = load_document(filepath, ClaimDocument)
    return validate_claims([loaded], context)


def _source_paper(claim: ClaimDocument, fallback: str) -> str:
    source = claim.source
    if source is not None:
        return source.paper
    provenance = claim.provenance
    if provenance is not None and provenance.paper is not None:
        return provenance.paper
    return fallback


def compile_claim_documents(
    claims: Sequence[LoadedDocument[ClaimDocument]],
    context: CompilationContext,
    *,
    context_ids: set[str] | None = None,
) -> ClaimCompilationBundle:
    diagnostics: list[PassDiagnostic] = []
    semantic_claims: list[SemanticClaim] = []
    seen_artifact_ids: dict[str, str] = {}
    seen_logical_ids: dict[str, str] = {}
    all_artifact_ids = {
        claim.document.artifact_id
        for claim in claims
        if isinstance(claim.document.artifact_id, str) and claim.document.artifact_id
    }

    for loaded_claim in claims:
        claim = loaded_claim.document
        filename = loaded_claim.filename
        raw_claim = msgspec.to_builtins(claim)
        if not isinstance(raw_claim, dict):
            continue

        raw_id = claim.id
        artifact_id = claim.artifact_id
        if isinstance(raw_id, str) and raw_id and not artifact_id:
            diagnostics.append(
                PassDiagnostic(
                    level="error",
                    code="claim.raw_id_input",
                    message=(
                        "claim uses raw 'id' input "
                        "without canonical identity fields"
                    ),
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.CHECKED,
                    filename=filename,
                    artifact_id=None,
                    pass_name="claim.compile",
                )
            )
            continue

        if not isinstance(artifact_id, str) or not artifact_id:
            diagnostics.append(
                PassDiagnostic(
                    level="error",
                    code="claim.missing_artifact_id",
                    message="claim missing 'artifact_id'",
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.CHECKED,
                    filename=filename,
                    artifact_id=None,
                    pass_name="claim.compile",
                )
            )
            continue

        if artifact_id in seen_artifact_ids:
            diagnostics.append(
                PassDiagnostic(
                    level="error",
                    code="claim.duplicate_artifact_id",
                    message=(
                        f"duplicate claim artifact_id '{artifact_id}' "
                        f"(also in {seen_artifact_ids[artifact_id]})"
                    ),
                    family=PropstoreFamily.CLAIMS,
                    stage=ClaimStage.CHECKED,
                    filename=filename,
                    artifact_id=artifact_id,
                    pass_name="claim.compile",
                )
            )
        else:
            seen_artifact_ids[artifact_id] = filename

        _validate_logical_ids(
            raw_claim.get("logical_ids"),
            filename=filename,
            artifact_id=artifact_id,
            seen_logical_ids=seen_logical_ids,
            diagnostics=diagnostics,
        )
        _validate_stances(
            raw_claim,
            artifact_id,
            filename,
            all_artifact_ids,
            diagnostics,
        )
        validate_claim_semantics(raw_claim, artifact_id, filename, context, diagnostics)

        semantic_claims.append(
            SemanticClaim(
                filename=filename,
                source_paper=_source_paper(claim, filename),
                artifact_id=artifact_id,
                claim_type=str(claim.type) if claim.type is not None else None,
                authored_claim=raw_claim,
                resolved_claim=claim,
            )
        )

    return ClaimCompilationBundle(
        context={
            "compilation_context": context,
            "context_ids": frozenset(context_ids or set()),
        },
        claim_documents=tuple(claims),
        semantic_claims=tuple(semantic_claims),
        diagnostics=tuple(diagnostics),
    )


class ClaimCompilePass:
    family = PropstoreFamily.CLAIMS
    name = "claim.compile"
    version = "1"
    input_stage = ClaimStage.AUTHORED
    output_stage = ClaimStage.CHECKED

    def run(
        self,
        value: Sequence[LoadedDocument[ClaimDocument]],
        context: object,
    ) -> PassResult[ClaimCheckedBundle]:
        if not isinstance(context, CompilationContext):
            raise TypeError("claim compile pass requires a CompilationContext")
        bundle = compile_claim_documents(
            value,
            context,
        )
        return PassResult(
            output=ClaimCheckedBundle(
                bundle=bundle,
                raw_id_quarantine_records=_collect_raw_id_quarantine_records(bundle),
            ),
            diagnostics=bundle.diagnostics,
        )


def register_claim_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ClaimCompilePass, family=PropstoreFamily.CLAIMS)


def run_claim_pipeline(
    claim_files: Sequence[LoadedDocument[ClaimDocument]],
    context: CompilationContext,
    *,
    context_ids: set[str] | None = None,
) -> PipelineResult[object]:
    bundle = compile_claim_documents(
        claim_files,
        context,
        context_ids=context_ids,
    )
    return PipelineResult(
        family=PropstoreFamily.CLAIMS,
        stage=ClaimStage.CHECKED,
        output=ClaimCheckedBundle(
            bundle=bundle,
            raw_id_quarantine_records=_collect_raw_id_quarantine_records(bundle),
        ),
        diagnostics=bundle.diagnostics,
    )

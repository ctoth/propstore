"""Claim compiler passes."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from propstore.families.claims.declaration import (
    ClaimDocument,
    StanceDocument as ClaimStanceDocument,
)
from propstore.core.conditions import check_condition_ir
from propstore.core.conditions.checked import CheckedCondition, checked_condition_set
from propstore.claims import (
    LoadedClaimsFile,
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
    build_compiler_claim_index,
    compiler_claim_match_kind,
    compiler_concept_match_kind,
)
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
from propstore.families.claims.passes.diagnostics import claim_diagnostic
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult
from propstore.families.identity.claims import compute_claim_version_id


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
    claim_files: Sequence[LoadedClaimsFile],
    context: CompilationContext,
    context_ids: set[str] | None = None,
) -> PipelineResult[object]:
    """Validate claim files against schema and compiler contract."""
    return run_claim_pipeline(
        ClaimAuthoredFiles.from_sequence(
            claim_files,
            context,
            context_ids=context_ids,
        )
    )


def validate_single_claim_file(
    filepath: Path,
    context: CompilationContext,
) -> PipelineResult[object]:
    """Validate a single typed claims YAML file."""
    loaded = load_claim_file(filepath)
    return validate_claims([loaded], context)


class ClaimCompilePass:
    family = PropstoreFamily.CLAIMS
    name = "claim.compile"
    version = "1"
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
            context_ids=(None if value.context_ids is None else set(value.context_ids)),
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

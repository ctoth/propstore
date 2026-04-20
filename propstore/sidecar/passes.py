"""Sidecar row compilation passes."""

from __future__ import annotations

from propstore.claims import claim_file_filename, claim_file_stage
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.sidecar.claim_utils import (
    collect_claim_reference_map,
    extract_deferred_stance_rows,
    prepare_claim_insert_row,
)
from propstore.sidecar.stages import (
    ClaimInsertRow,
    ClaimSidecarRows,
    ClaimStanceInsertRow,
)


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

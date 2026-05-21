"""Shared claim-side helpers for sidecar compilation."""

from __future__ import annotations

import json

from quire.references import FamilyReferenceIndex

from propstore.compiler.ir import SemanticClaim
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.stances import VALID_STANCE_TYPES


def normalize_conditions_differ(value: object) -> object:
    if isinstance(value, list):
        return json.dumps(value)
    return value


def coerce_stance_resolution(
    resolution: object,
    owner: str,
) -> dict[str, object]:
    if resolution is None:
        return {}
    if not isinstance(resolution, dict):
        raise ValueError(f"{owner} resolution must be a mapping")
    return resolution


def resolution_opinion_columns(resolution: dict[str, object]) -> tuple[object, object, object, object]:
    opinion = resolution.get("opinion")
    if opinion is None:
        return None, None, None, None
    if not isinstance(opinion, dict):
        raise ValueError("resolution opinion must be a mapping")
    return (
        opinion.get("b"),
        opinion.get("d"),
        opinion.get("u"),
        opinion.get("a"),
    )


def extract_deferred_stance_rows_with_diagnostics(
    claim: dict | SemanticClaim,
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[list[tuple], tuple[QuarantineDiagnostic, ...]]:
    filename: str | None = None
    if isinstance(claim, SemanticClaim):
        semantic_claim = claim
        filename = semantic_claim.filename
        claim_data = semantic_claim.resolved_claim.to_payload()
        claim_id = (
            claim_data.get("artifact_id")
            if isinstance(claim_data.get("artifact_id"), str)
            else claim_data.get("id")
        )
        stance_inputs = [
            (
                stance.data,
                stance.target_ref.resolved_id or stance.target_ref.raw_text,
            )
            for stance in semantic_claim.stances
        ]
    else:
        claim_data = claim
        claim_ref = claim_data.get("artifact_id") or claim_data.get("id")
        claim_id = claim_index.resolve_id(claim_ref)
        if claim_id is None and isinstance(claim_ref, str):
            claim_id = claim_ref
        stance_inputs = []
        for stance in claim_data.get("stances", []) or []:
            if not isinstance(stance, dict):
                continue
            target_ref = stance.get("target")
            target_claim_id = claim_index.resolve_id(target_ref)
            if target_claim_id is None and isinstance(target_ref, str):
                target_claim_id = target_ref
            stance_inputs.append((stance, target_claim_id))

    rows: list[tuple] = []
    diagnostics: list[QuarantineDiagnostic] = []
    valid_claim_ids = set(claim_index.ids())
    for stance, target_claim_id in stance_inputs:
        stance_type = stance.get("type")
        if not target_claim_id or not stance_type:
            continue
        if stance_type not in VALID_STANCE_TYPES:
            message = (
                f"claim '{claim_id}' uses unrecognized stance type "
                f"'{stance_type}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=str(claim_id or target_claim_id),
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        if target_claim_id not in valid_claim_ids:
            message = (
                f"claim '{claim_id}' references nonexistent target claim "
                f"'{target_claim_id}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=str(target_claim_id),
                    kind="stance",
                    diagnostic_kind="stance_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        resolution = coerce_stance_resolution(
            stance.get("resolution"),
            f"claim '{claim_id}' stance targeting '{target_claim_id}'",
        )
        opinion_columns = resolution_opinion_columns(resolution)
        rows.append((
            claim_id,
            target_claim_id,
            stance_type,
            stance.get("target_justification_id"),
            stance.get("strength"),
            normalize_conditions_differ(stance.get("conditions_differ")),
            stance.get("note"),
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
            claim_id,
        ))
    return rows, tuple(diagnostics)

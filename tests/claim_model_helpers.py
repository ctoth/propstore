from __future__ import annotations

import json
from collections.abc import Sequence
from typing import cast

from propstore.core.algorithm_stage import AlgorithmStage
from propstore.core.claim_types import ClaimType
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import (
    Claim,
    ClaimAlgorithmPayload,
    ClaimConceptLink,
    ClaimNumericPayload,
    ClaimTextPayload,
)
from propstore.families.world_charters import world_record


def claim_concept_link(
    *,
    claim_id: str,
    concept_id: str,
    role: ClaimConceptLinkRole,
    ordinal: int = 0,
    binding_name: str | None = None,
) -> ClaimConceptLink:
    return cast(
        ClaimConceptLink,
        world_record(
            "claim_concept_link",
            {
                "claim_id": claim_id,
                "concept_id": concept_id,
                "role": role,
                "ordinal": ordinal,
                "binding_name": binding_name,
            },
        ),
    )


def claim_model(
    claim_id: str = "claim1",
    *,
    claim_type: ClaimType = ClaimType.PARAMETER,
    concept_id: str = "concept1",
    concept_links: Sequence[ClaimConceptLink] | None = None,
    target_concept: str | None = None,
    value: float | None = 1.0,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    unit: str | None = None,
    value_si: float | None = None,
    uncertainty: float | None = None,
    uncertainty_type: str | None = None,
    sample_size: int | None = None,
    conditions_cel: str | None = None,
    conditions_ir: str | None = None,
    statement: str | None = None,
    expression: str | None = None,
    source_slug: str | None = "paper1",
    source_paper: str = "paper1",
    provenance_page: int = 1,
    provenance_json: dict[str, object] | None = None,
    context_id: str | None = None,
    branch: str | None = None,
    build_status: str = "ingested",
    stage: str | None = None,
    promotion_status: str | None = None,
    algorithm_body: str | None = None,
    algorithm_stage: AlgorithmStage | None = None,
    variables_json: str | None = None,
) -> Claim:
    claim = cast(
        Claim,
        world_record(
            "claim_core",
            {
                "id": claim_id,
                "primary_logical_id": claim_id,
                "logical_ids_json": "[]",
                "version_id": "",
                "content_hash": "",
                "seq": 0,
                "type": claim_type,
                "target_concept": target_concept,
                "source_slug": source_slug,
                "source_paper": source_paper,
                "provenance_page": provenance_page,
                "provenance_json": (
                    None if provenance_json is None else json.dumps(provenance_json)
                ),
                "context_id": context_id,
                "premise_kind": "ordinary",
                "branch": branch,
                "build_status": build_status,
                "stage": stage,
                "promotion_status": promotion_status,
            },
        ),
    )
    links = list(concept_links) if concept_links is not None else [
        claim_concept_link(
            claim_id=claim_id,
            concept_id=concept_id,
            role=ClaimConceptLinkRole.OUTPUT,
        )
    ]
    for link in links:
        link.claim = claim
    claim.concept_links = links

    numeric_payload = cast(
        ClaimNumericPayload,
        world_record(
            "claim_numeric_payload",
            {
                "claim_id": claim_id,
                "value": value,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "uncertainty": uncertainty,
                "uncertainty_type": uncertainty_type,
                "sample_size": sample_size,
                "unit": unit,
                "value_si": value_si,
                "lower_bound_si": None,
                "upper_bound_si": None,
            },
        ),
    )
    numeric_payload.claim = claim
    claim.numeric_payload = numeric_payload

    text_payload = cast(
        ClaimTextPayload,
        world_record(
            "claim_text_payload",
            {
                "claim_id": claim_id,
                "conditions_cel": conditions_cel,
                "conditions_ir": conditions_ir,
                "statement": statement,
                "expression": expression,
                "sympy_generated": None,
                "sympy_error": None,
                "name": None,
                "measure": None,
                "listener_population": None,
                "methodology": None,
                "notes": None,
                "description": None,
                "auto_summary": None,
            },
        ),
    )
    text_payload.claim = claim
    claim.text_payload = text_payload

    algorithm_payload = cast(
        ClaimAlgorithmPayload,
        world_record(
            "claim_algorithm_payload",
            {
                "claim_id": claim_id,
                "body": algorithm_body,
                "canonical_ast": None,
                "variables_json": variables_json,
                "algorithm_stage": algorithm_stage,
            },
        ),
    )
    algorithm_payload.claim = claim
    claim.algorithm_payload = algorithm_payload
    claim.source_assertions = []
    return claim

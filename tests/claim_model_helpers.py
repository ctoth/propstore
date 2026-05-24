from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from propstore.core.algorithm_stage import AlgorithmStage
from propstore.families.claims.types import ClaimType
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import (
    Claim,
    ClaimAlgorithmPayload,
    ClaimConceptLink,
    ClaimNumericPayload,
    ClaimSourceAssertion,
    ClaimTextPayload,
)


def claim_concept_link(
    *,
    claim_id: str,
    concept_id: str,
    role: ClaimConceptLinkRole,
    ordinal: int = 0,
    binding_name: str | None = None,
) -> ClaimConceptLink:
    return ClaimConceptLink(
        claim_id=claim_id,
        concept_id=concept_id,
        role=role,
        ordinal=ordinal,
        binding_name=binding_name,
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
    confidence: float | None = None,
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
    source_assertion_ids: Sequence[str] = (),
) -> Claim:
    claim = Claim(
        id=claim_id,
        primary_logical_id=claim_id,
        logical_ids_json="[]",
        version_id="",
        content_hash="",
        seq=0,
        type=claim_type,
        target_concept=target_concept,
        source_slug=source_slug,
        source_paper=source_paper,
        provenance_page=provenance_page,
        provenance_json=None if provenance_json is None else json.dumps(provenance_json),
        context_id=context_id,
        premise_kind="ordinary",
        branch=branch,
        build_status=build_status,
        stage=stage,
        promotion_status=promotion_status,
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

    numeric_payload = ClaimNumericPayload(
        claim_id=claim_id,
        value=value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        uncertainty=uncertainty,
        uncertainty_type=uncertainty_type,
        sample_size=sample_size,
        confidence=confidence,
        unit=unit,
        value_si=value_si,
        lower_bound_si=None,
        upper_bound_si=None,
    )
    numeric_payload.claim = claim
    claim.numeric_payload = numeric_payload

    text_payload = ClaimTextPayload(
        claim_id=claim_id,
        conditions_cel=conditions_cel,
        conditions_ir=conditions_ir,
        statement=statement,
        expression=expression,
        sympy_generated=None,
        sympy_error=None,
        name=None,
        measure=None,
        listener_population=None,
        methodology=None,
        notes=None,
        description=None,
        auto_summary=None,
    )
    text_payload.claim = claim
    claim.text_payload = text_payload

    algorithm_payload = ClaimAlgorithmPayload(
        claim_id=claim_id,
        body=algorithm_body,
        canonical_ast=None,
        variables_json=variables_json,
        algorithm_stage=algorithm_stage,
    )
    algorithm_payload.claim = claim
    claim.algorithm_payload = algorithm_payload
    source_assertions = [
        ClaimSourceAssertion(
            claim_id=claim_id,
            source_assertion_id=source_assertion_id,
            ordinal=ordinal,
        )
        for ordinal, source_assertion_id in enumerate(source_assertion_ids)
    ]
    for source_assertion in source_assertions:
        source_assertion.claim = claim
    claim.source_assertions = source_assertions
    return claim


def claim_model_from_test_payload(row: Mapping[str, object]) -> Claim:
    raw_links = row.get("concept_links")
    links: list[ClaimConceptLink] = []
    if isinstance(raw_links, Sequence) and not isinstance(raw_links, str):
        for item in raw_links:
            if not isinstance(item, Mapping):
                continue
            links.append(
                claim_concept_link(
                    claim_id=str(item.get("claim_id", row["id"])),
                    concept_id=str(item["concept_id"]),
                    role=ClaimConceptLinkRole(str(item.get("role", "output"))),
                    ordinal=int(item.get("ordinal", 0)),
                    binding_name=(
                        None
                        if item.get("binding_name") is None
                        else str(item["binding_name"])
                    ),
                )
            )
    concept_id = str(row.get("concept_id") or row.get("target_concept") or "concept1")
    return claim_model(
        claim_id=str(row["id"]),
        claim_type=ClaimType(str(row.get("type", ClaimType.PARAMETER.value))),
        concept_id=concept_id,
        concept_links=links or None,
        target_concept=(
            None if row.get("target_concept") is None else str(row["target_concept"])
        ),
        value=None if row.get("value") is None else float(row["value"]),
        sample_size=(
            None if row.get("sample_size") is None else int(row["sample_size"])
        ),
        uncertainty=(
            None if row.get("uncertainty") is None else float(row["uncertainty"])
        ),
        confidence=(
            None if row.get("confidence") is None else float(row["confidence"])
        ),
        uncertainty_type=(
            None
            if row.get("uncertainty_type") is None
            else str(row["uncertainty_type"])
        ),
        unit=None if row.get("unit") is None else str(row["unit"]),
        conditions_cel=(
            None if row.get("conditions_cel") is None else str(row["conditions_cel"])
        ),
        conditions_ir=(
            None if row.get("conditions_ir") is None else str(row["conditions_ir"])
        ),
        context_id=None if row.get("context_id") is None else str(row["context_id"]),
    )

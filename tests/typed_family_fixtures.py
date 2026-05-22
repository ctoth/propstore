from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.families.claims.types import ClaimType
from propstore.core.graph_types import ClaimNode
from propstore.families.claims.graph import claim_node_from_claim
from propstore.families.claims.declaration import (
    Claim,
    ClaimAlgorithmPayload,
    ClaimNumericPayload,
    ClaimTextPayload,
)
from propstore.families.relations.declaration import Stance

_CLAIM_GRAPH_METADATA_KEYS = (
    "confidence",
    "claim_probability",
    "effective_sample_size",
    "source_prior_base_rate",
    "source_quality_opinion",
    "opinion_belief",
    "opinion_disbelief",
    "opinion_uncertainty",
    "opinion_base_rate",
)


def claim_from_payload(payload: Mapping[str, Any]) -> Claim:
    claim_id = str(payload["id"])
    claim_type = ClaimType(payload.get("type", "parameter"))
    claim = Claim(
        id=claim_id,
        type=claim_type,
        target_concept=payload.get("concept_id") or payload.get("target_concept"),
        context_id=payload.get("context_id"),
        premise_kind=payload.get("premise_kind", "ordinary"),
        source_slug=payload.get("source_slug"),
        source_paper=payload.get("source_paper"),
        provenance_page=payload.get("provenance_page"),
        provenance_json=payload.get("provenance_json"),
        primary_logical_id=payload.get("primary_logical_id", ""),
        logical_ids_json=payload.get("logical_ids_json", "[]"),
        version_id=payload.get("version_id", ""),
        seq=payload.get("seq", 0),
        branch=payload.get("branch"),
        build_status=payload.get("build_status", "ingested"),
        stage=payload.get("stage"),
        promotion_status=payload.get("promotion_status"),
    )
    claim.concept_links = []
    claim.source_assertions = []
    claim.numeric_payload = ClaimNumericPayload(
        claim_id=claim_id,
        value=payload.get("value"),
        lower_bound=payload.get("lower_bound"),
        upper_bound=payload.get("upper_bound"),
        uncertainty=payload.get("uncertainty"),
        uncertainty_type=payload.get("uncertainty_type"),
        sample_size=payload.get("sample_size"),
        confidence=payload.get("confidence"),
        unit=payload.get("unit"),
        value_si=payload.get("value_si"),
        lower_bound_si=payload.get("lower_bound_si"),
        upper_bound_si=payload.get("upper_bound_si"),
    )
    claim.algorithm_payload = ClaimAlgorithmPayload(
        claim_id=claim_id,
        body=payload.get("body"),
        canonical_ast=payload.get("canonical_ast"),
        variables_json=payload.get("variables_json"),
        algorithm_stage=payload.get("algorithm_stage"),
    )
    claim.text_payload = ClaimTextPayload(
        claim_id=claim_id,
        conditions_cel=payload.get("conditions_cel"),
        conditions_ir=payload.get("conditions_ir"),
        statement=payload.get("statement"),
        expression=payload.get("expression"),
        sympy_generated=payload.get("sympy"),
        sympy_error=payload.get("sympy_error"),
        name=payload.get("name"),
        measure=payload.get("measure"),
        listener_population=payload.get("listener_population"),
        methodology=payload.get("methodology"),
        notes=payload.get("notes"),
        description=payload.get("description"),
        auto_summary=payload.get("auto_summary"),
    )
    claim.numeric_payload.claim = claim
    claim.algorithm_payload.claim = claim
    claim.text_payload.claim = claim
    return claim


def claim_node_from_payload(payload: Mapping[str, Any]) -> ClaimNode:
    node = claim_node_from_claim(claim_from_payload(payload))
    metadata = tuple(
        (key, payload[key])
        for key in _CLAIM_GRAPH_METADATA_KEYS
        if key in payload
    )
    return ClaimNode(
        claim_id=node.claim_id,
        claim_type=node.claim_type,
        value_concept_id=node.value_concept_id,
        scalar_value=node.scalar_value,
        context_id=node.context_id,
        source_slug=node.source_slug,
        source_paper=node.source_paper,
        lower_bound=node.lower_bound,
        upper_bound=node.upper_bound,
        uncertainty=node.uncertainty,
        uncertainty_type=node.uncertainty_type,
        sample_size=node.sample_size,
        unit=node.unit,
        value_si=node.value_si,
        lower_bound_si=node.lower_bound_si,
        upper_bound_si=node.upper_bound_si,
        checked_conditions=node.checked_conditions,
        provenance=node.provenance,
        label=node.label,
        source_assertion_ids=node.source_assertion_ids,
        attributes=node.attributes + metadata,
    )


def stance_from_payload(payload: Mapping[str, Any]) -> Stance:
    return Stance(
        source_kind="claim",
        source_id=str(payload["claim_id"]),
        relation_type=str(payload["stance_type"]),
        target_kind="claim",
        target_id=str(payload["target_claim_id"]),
        perspective_source_claim_id=str(payload["claim_id"]),
        target_justification_id=payload.get("target_justification_id"),
        confidence=payload.get("confidence"),
        opinion_belief=payload.get("opinion_belief"),
        opinion_disbelief=payload.get("opinion_disbelief"),
        opinion_uncertainty=payload.get("opinion_uncertainty"),
        opinion_base_rate=payload.get("opinion_base_rate"),
    )

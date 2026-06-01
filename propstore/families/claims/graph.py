"""Typed claim-to-graph projection."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from propstore.families.claims.types import ClaimType
from propstore.core.conditions import (
    CheckedConditionSet,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo
from propstore.core.graph_types import ClaimNode, ProvenanceRecord
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
)
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import (
    Claim,
    ClaimConceptLink,
    ClaimNumericPayload,
    ClaimTextPayload,
)

if TYPE_CHECKING:
    from propstore.world.types import SyntheticClaim


def claim_node_from_claim(
    claim: Claim,
    *,
    claim_id: str | None = None,
) -> ClaimNode:
    numeric_payload = claim.numeric_payload
    return ClaimNode(
        claim_id=ClaimId(claim_id or claim.id),
        claim_type=claim.type or ClaimType.UNKNOWN,
        value_concept_id=(
            None
            if claim.value_concept_id is None
            else ConceptId(claim.value_concept_id)
        ),
        scalar_value=None if numeric_payload is None else numeric_payload.value,
        context_id=claim.context_id,
        source_slug=claim.source_slug,
        source_paper=claim.source_paper,
        lower_bound=None if numeric_payload is None else numeric_payload.lower_bound,
        upper_bound=None if numeric_payload is None else numeric_payload.upper_bound,
        uncertainty=None if numeric_payload is None else numeric_payload.uncertainty,
        uncertainty_type=(
            None if numeric_payload is None else numeric_payload.uncertainty_type
        ),
        sample_size=None if numeric_payload is None else numeric_payload.sample_size,
        confidence=None if numeric_payload is None else numeric_payload.confidence,
        unit=None if numeric_payload is None else numeric_payload.unit,
        value_si=None if numeric_payload is None else numeric_payload.value_si,
        lower_bound_si=(
            None if numeric_payload is None else numeric_payload.lower_bound_si
        ),
        upper_bound_si=(
            None if numeric_payload is None else numeric_payload.upper_bound_si
        ),
        checked_conditions=claim.checked_conditions,
        provenance=_claim_provenance(claim, source_id=claim_id or claim.id),
        source_assertion_ids=tuple(
            assertion.source_assertion_id for assertion in claim.source_assertions
        ),
        attributes=_claim_graph_attributes(claim),
    )


def _claim_provenance(claim: Claim, *, source_id: str) -> ProvenanceRecord | None:
    provenance_json = claim.provenance_json
    extras: dict[str, Any] = {}
    if provenance_json:
        try:
            loaded = json.loads(provenance_json)
            if isinstance(loaded, dict):
                extras.update(loaded)
        except json.JSONDecodeError:
            extras["provenance_json"] = provenance_json
    if claim.source_paper is not None:
        extras.setdefault("paper", claim.source_paper)
    if claim.provenance_page is not None:
        extras.setdefault("page", claim.provenance_page)
    extras["source_table"] = "claim"
    extras["source_id"] = source_id
    return ProvenanceRecord.from_json_payload(extras)


def _claim_graph_attributes(claim: Claim) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (key, value)
        for key, value in (
            ("primary_logical_id", claim.primary_logical_id),
            ("logical_ids_json", claim.logical_ids_json),
            ("version_id", claim.version_id),
            ("seq", claim.seq),
            ("target_concept", claim.target_concept),
            ("provenance_json", claim.provenance_json),
            ("premise_kind", claim.premise_kind),
            ("branch", claim.branch),
            ("build_status", claim.build_status),
            ("stage", claim.stage),
            ("promotion_status", claim.promotion_status),
        )
        if value is not None
    )


def synthetic_claim_to_claim(
    synthetic: SyntheticClaim,
    *,
    existing_claim: Claim | None,
    cel_registry: Mapping[str, ConceptInfo],
) -> Claim:
    condition_set = _synthetic_checked_conditions(
        synthetic,
        cel_registry=cel_registry,
    )
    conditions_cel = json.dumps(synthetic.conditions) if synthetic.conditions else None
    conditions_ir = _conditions_ir_json(condition_set)
    existing_numeric = (
        None if existing_claim is None else existing_claim.numeric_payload
    )
    existing_text = None if existing_claim is None else existing_claim.text_payload
    claim = Claim(
        id=synthetic.id,
        primary_logical_id=(
            existing_claim.primary_logical_id
            if existing_claim is not None
            else synthetic.id
        ),
        logical_ids_json=(
            existing_claim.logical_ids_json if existing_claim is not None else "[]"
        ),
        version_id=existing_claim.version_id if existing_claim is not None else "",
        content_hash=existing_claim.content_hash if existing_claim is not None else "",
        seq=existing_claim.seq if existing_claim is not None else 0,
        type=synthetic.type,
        target_concept=(
            ConceptId(synthetic.concept_id)
            if synthetic.type is ClaimType.MEASUREMENT
            else (existing_claim.target_concept if existing_claim is not None else None)
        ),
        source_slug=existing_claim.source_slug if existing_claim is not None else None,
        source_paper=existing_claim.source_paper if existing_claim is not None else "",
        provenance_page=(
            existing_claim.provenance_page if existing_claim is not None else 0
        ),
        provenance_json=(
            existing_claim.provenance_json if existing_claim is not None else None
        ),
        context_id=existing_claim.context_id if existing_claim is not None else None,
        premise_kind=(
            existing_claim.premise_kind if existing_claim is not None else "ordinary"
        ),
        branch=existing_claim.branch if existing_claim is not None else None,
        build_status=(
            existing_claim.build_status if existing_claim is not None else "ingested"
        ),
        stage=existing_claim.stage if existing_claim is not None else None,
        promotion_status=(
            existing_claim.promotion_status if existing_claim is not None else None
        ),
    )
    numeric_payload = ClaimNumericPayload(
        claim_id=synthetic.id,
        value=(
            synthetic.value
            if isinstance(synthetic.value, int | float)
            and not isinstance(synthetic.value, bool)
            else (None if existing_numeric is None else existing_numeric.value)
        ),
        lower_bound=None if existing_numeric is None else existing_numeric.lower_bound,
        upper_bound=None if existing_numeric is None else existing_numeric.upper_bound,
        uncertainty=None if existing_numeric is None else existing_numeric.uncertainty,
        uncertainty_type=(
            None if existing_numeric is None else existing_numeric.uncertainty_type
        ),
        sample_size=(
            synthetic.sample_size
            if synthetic.sample_size is not None
            else (None if existing_numeric is None else existing_numeric.sample_size)
        ),
        confidence=None if existing_numeric is None else existing_numeric.confidence,
        unit=None if existing_numeric is None else existing_numeric.unit,
        value_si=None if existing_numeric is None else existing_numeric.value_si,
        lower_bound_si=(
            None if existing_numeric is None else existing_numeric.lower_bound_si
        ),
        upper_bound_si=(
            None if existing_numeric is None else existing_numeric.upper_bound_si
        ),
    )
    text_payload = ClaimTextPayload(
        claim_id=synthetic.id,
        conditions_cel=conditions_cel,
        conditions_ir=conditions_ir,
        statement=None if existing_text is None else existing_text.statement,
        expression=(
            synthetic.value
            if isinstance(synthetic.value, str)
            else (None if existing_text is None else existing_text.expression)
        ),
        sympy_generated=None
        if existing_text is None
        else existing_text.sympy_generated,
        sympy_error=None if existing_text is None else existing_text.sympy_error,
        name=None if existing_text is None else existing_text.name,
        measure=None if existing_text is None else existing_text.measure,
        listener_population=(
            None if existing_text is None else existing_text.listener_population
        ),
        methodology=None if existing_text is None else existing_text.methodology,
        notes=None if existing_text is None else existing_text.notes,
        description=None if existing_text is None else existing_text.description,
        auto_summary=None if existing_text is None else existing_text.auto_summary,
    )
    claim.concept_links = list(_synthetic_concept_links(synthetic))
    claim.numeric_payload = numeric_payload
    claim.text_payload = text_payload
    claim.algorithm_payload = (
        None if existing_claim is None else existing_claim.algorithm_payload
    )
    claim.source_assertions = (
        [] if existing_claim is None else list(existing_claim.source_assertions)
    )
    numeric_payload.claim = claim
    text_payload.claim = claim
    for link in claim.concept_links:
        link.claim = claim
    for assertion in claim.source_assertions:
        assertion.claim = claim
    return claim


def _synthetic_checked_conditions(
    synthetic: SyntheticClaim,
    *,
    cel_registry: Mapping[str, ConceptInfo],
) -> CheckedConditionSet | None:
    if not synthetic.conditions:
        return None
    return checked_condition_set(
        check_condition_ir(condition, cel_registry)
        for condition in synthetic.conditions
    )


def _conditions_ir_json(condition_set: CheckedConditionSet | None) -> str | None:
    if condition_set is None:
        return None
    return json.dumps(
        checked_condition_set_to_json(condition_set),
        sort_keys=True,
    )


def _synthetic_concept_links(synthetic: SyntheticClaim) -> tuple[ClaimConceptLink, ...]:
    role = (
        ClaimConceptLinkRole.TARGET
        if synthetic.type is ClaimType.MEASUREMENT
        else ClaimConceptLinkRole.OUTPUT
    )
    return (
        ClaimConceptLink(
            claim_id=ClaimId(synthetic.id),
            concept_id=ConceptId(synthetic.concept_id),
            role=role,
            ordinal=0,
        ),
    )

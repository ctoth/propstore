"""Typed claim-to-graph projection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from propstore.families.claims.types import ClaimType
from propstore.core.conditions import (
    CheckedConditionSet,
    check_condition_ir,
    checked_condition_set,
)
from propstore.core.conditions.registry import ConditionRegistry
from propstore.core.id_types import (
    ClaimId,
    ConceptId,
)
from propstore.core.relations import ClaimConceptLinkRole
from propstore.families.claims.declaration import (
    Claim,
    ClaimConceptLink,
)

if TYPE_CHECKING:
    from propstore.world.types import SyntheticClaim


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


def _synthetic_checked_conditions(
    synthetic: SyntheticClaim,
    *,
    cel_registry: ConditionRegistry,
) -> CheckedConditionSet | None:
    if not synthetic.conditions:
        return None
    return checked_condition_set(
        check_condition_ir(condition, cel_registry)
        for condition in synthetic.conditions
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

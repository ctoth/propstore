"""Shared context-aware conflict classification helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from propstore.cel_types import CelExpr

from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingSystem


def _classify_pair_context(
    context_a: str | None,
    context_b: str | None,
    lifting_system: LiftingSystem | None,
) -> ConflictClass | None:
    """Check if two claims' contexts make them non-conflicting."""
    if lifting_system is None:
        return None
    if context_a is None or context_b is None:
        return None
    if context_a == context_b:
        return None
    if lifting_system.can_lift(context_a, context_b):
        return None
    if lifting_system.can_lift(context_b, context_a):
        return None
    return ConflictClass.CONTEXT_PHI_NODE


def _claim_context(claim: ConflictClaim) -> str | None:
    return claim.context_id


def _append_context_classified_record(
    records: list[ConflictRecord],
    *,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    conditions_a: list[CelExpr],
    conditions_b: list[CelExpr],
    value_a: str,
    value_b: str,
    context_a: str | None,
    context_b: str | None,
    lifting_system: LiftingSystem | None,
    derivation_chain: str | None = None,
) -> bool:
    context_class = _classify_pair_context(context_a, context_b, lifting_system)
    if context_class is None:
        return False
    records.append(ConflictRecord(
        concept_id=concept_id,
        claim_a_id=claim_a_id,
        claim_b_id=claim_b_id,
        warning_class=context_class,
        conditions_a=conditions_a,
        conditions_b=conditions_b,
        value_a=value_a,
        value_b=value_b,
        derivation_chain=derivation_chain,
    ))
    return True

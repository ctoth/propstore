"""Shared context-aware conflict classification helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ConflictClass, ConflictClaim, ConflictRecord

if TYPE_CHECKING:
    from propstore.context_hierarchy import ContextHierarchy


def _classify_pair_context(
    context_a: str | None,
    context_b: str | None,
    hierarchy: ContextHierarchy | None,
) -> ConflictClass | None:
    """Check if two claims' contexts make them non-conflicting."""
    if hierarchy is None:
        return None
    if context_a is None or context_b is None:
        return None
    if context_a == context_b:
        return None
    if hierarchy.are_excluded(context_a, context_b):
        return ConflictClass.CONTEXT_PHI_NODE
    if hierarchy.is_visible(context_a, context_b):
        return None
    if hierarchy.is_visible(context_b, context_a):
        return None
    return None  # unrelated contexts — let condition analysis decide


def _claim_context(claim: ConflictClaim) -> str | None:
    return claim.context_id


def _append_context_classified_record(
    records: list[ConflictRecord],
    *,
    concept_id: str,
    claim_a_id: str,
    claim_b_id: str,
    conditions_a: list[str],
    conditions_b: list[str],
    value_a: str,
    value_b: str,
    context_a: str | None,
    context_b: str | None,
    context_hierarchy: ContextHierarchy | None,
    derivation_chain: str | None = None,
) -> bool:
    context_class = _classify_pair_context(context_a, context_b, context_hierarchy)
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

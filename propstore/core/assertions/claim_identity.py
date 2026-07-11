"""Assertion identity for canonical claim charters."""

from __future__ import annotations

import hashlib
import json

from propstore.core.id_types import ContextId, to_context_id
from propstore.families.claims import Claim


def content_digest(value: object) -> str:
    """Return the persisted deterministic digest for assertion identity."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def semantic_content(claim: Claim) -> dict[str, object]:
    """Return propositional content, excluding identity and lifecycle fields."""

    return {
        "claim_type": None if claim.claim_type is None else claim.claim_type.value,
        "statement": claim.statement,
        "name": claim.name,
        "body": claim.body,
        "expression": claim.expression,
        "sympy": claim.sympy,
        "measure": claim.measure,
        "methodology": claim.methodology,
        "notes": claim.notes,
        "output_concept": claim.output_concept,
        "target_concept": claim.target_concept,
        "concepts": list(claim.concepts),
        "equations": list(claim.equations),
        "value": claim.value,
        "lower_bound": claim.lower_bound,
        "upper_bound": claim.upper_bound,
        "uncertainty": claim.uncertainty,
        "uncertainty_type": claim.uncertainty_type,
        "confidence": claim.confidence,
        "unit": claim.unit,
        "sample_size": claim.sample_size,
    }


def claim_assertion_id(
    claim: Claim,
    *,
    context_id: ContextId | str | None,
) -> str:
    """Return stable assertion identity for a canonical claim."""

    effective_context = (
        claim.context_id
        if claim.context_id is not None
        else (None if context_id is None else str(to_context_id(context_id)))
    )
    key = {
        "content": semantic_content(claim),
        "context_id": effective_context,
        "conditions": sorted(claim.conditions),
    }
    return f"ps:assertion:{content_digest(key)}"


__all__ = [
    "claim_assertion_id",
    "content_digest",
    "semantic_content",
]

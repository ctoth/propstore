"""Propositional assertion identity for claim graph nodes.

Two versions of the *same proposition* — agreeing on content, context, and CEL
conditions — collapse to one assertion id; versions that disagree on any of these
stay rival (the description-claim coreference / micropublication-identity concept
in CLAUDE.md, layer 2). The id is a deterministic ``ps:assertion:<digest>`` over
the claim's propositional content, the context it is asserted in, and its
conditions. The ATMS engine uses it as the claim node id so identical claim
content materializes as one node with one label.

This is the read-side, source-revision-free home of the assertion-identity scheme
the merge boundary (:mod:`propstore.merge.merge_claims`) uses for the same
purpose: one canonical content digest, no second spelling.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from propstore.core.graph_types import ClaimNode
from propstore.core.id_types import ContextId, to_context_id


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def claim_node_content(claim: ClaimNode) -> dict[str, Any]:
    """The propositional content of a claim node, excluding identity/lifecycle.

    Mirrors :func:`propstore.merge.merge_claims.semantic_content`, reconstructed
    from the :class:`ClaimNode`'s typed fields plus the row-shaped attributes the
    graph builder lowers onto it.
    """

    attributes: Mapping[str, Any] = claim.attribute_mapping()
    return {
        "claim_type": claim.claim_type.value,
        "statement": attributes.get("statement"),
        "name": attributes.get("name"),
        "body": attributes.get("body"),
        "expression": attributes.get("expression"),
        "sympy": attributes.get("sympy"),
        "measure": attributes.get("measure"),
        "methodology": attributes.get("methodology"),
        "notes": attributes.get("notes"),
        "output_concept": (
            None if claim.value_concept_id is None else str(claim.value_concept_id)
        ),
        "target_concept": attributes.get("target_concept"),
        "concepts": list(attributes.get("concepts") or ()),
        "equations": list(attributes.get("equations") or ()),
        "value": claim.scalar_value,
        "lower_bound": attributes.get("lower_bound"),
        "upper_bound": attributes.get("upper_bound"),
        "uncertainty": attributes.get("uncertainty"),
        "uncertainty_type": attributes.get("uncertainty_type"),
        "confidence": attributes.get("confidence"),
        "unit": attributes.get("unit"),
        "sample_size": attributes.get("sample_size"),
    }


def claim_node_context_id(claim: ClaimNode) -> str | None:
    """The id of the context the claim node is authored in, if any."""

    context_id = claim.attribute_value("context_id")
    return None if context_id is None else str(context_id)


def claim_node_assertion_id(
    claim: ClaimNode,
    *,
    context_id: ContextId | str | None,
) -> str:
    """Stable ``ps:assertion:`` identity for one claim node.

    The claim's own context takes precedence; ``context_id`` (the environment's
    context) is the fallback so a context-free claim asserted under a rendering
    context still collapses consistently with the merge boundary.
    """

    own_context = claim_node_context_id(claim)
    effective_context = (
        own_context
        if own_context is not None
        else (None if context_id is None else str(to_context_id(context_id)))
    )
    conditions = (
        tuple(str(source) for source in claim.checked_conditions.sources)
        if claim.checked_conditions is not None
        else ()
    )
    key = {
        "content": claim_node_content(claim),
        "context_id": effective_context,
        "conditions": sorted(conditions),
    }
    return f"ps:assertion:{_digest(key)}"


__all__ = [
    "claim_node_assertion_id",
    "claim_node_content",
    "claim_node_context_id",
]

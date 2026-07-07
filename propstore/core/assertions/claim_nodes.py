"""Propositional assertion identity for claim graph nodes.

Two versions of the *same proposition* — agreeing on content, context, and CEL
conditions — collapse to one assertion id; versions that disagree on any of these
stay rival (the description-claim coreference / micropublication-identity concept
in CLAUDE.md, layer 2). The id is a deterministic ``ps:assertion:<digest>`` over
the claim's propositional content, the context it is asserted in, and its
conditions. The ATMS engine uses it as the claim node id so identical claim
content materializes as one node with one label.

This module is the single home of the assertion-identity scheme: one canonical
content digest and one content-key schema, projected from the charter
:class:`~propstore.families.claims.Claim` by :func:`semantic_content` and from
the graph-lowered :class:`~propstore.core.graph_types.ClaimNode` by
:func:`claim_node_content`. The merge boundary
(:mod:`propstore.merge.merge_claims`) imports both — no second spelling.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from propstore.core.graph_types import ClaimNode
from propstore.core.id_types import ContextId, to_context_id
from propstore.families.claims import Claim


def content_digest(value: object) -> str:
    """Deterministic sha256 over the sorted-key JSON encoding of ``value``.

    Persisted ``ps:assertion:`` ids are derived from these bytes; the encoding
    (``sort_keys``, compact separators, ``default=str``) must not change
    without an explicit identity migration.
    """

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def semantic_content(claim: Claim) -> dict[str, object]:
    """The propositional content of a charter claim, excluding identity and lifecycle."""

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


def claim_node_content(claim: ClaimNode) -> dict[str, Any]:
    """The propositional content of a claim node, excluding identity/lifecycle.

    The node-side projection of the same content-key schema as
    :func:`semantic_content`, reconstructed from the :class:`ClaimNode`'s typed
    fields plus the row-shaped attributes the graph builder lowers onto it.
    The two must stay key-for-key identical (pinned by
    ``tests/test_assertion_content_parity.py``).
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
    return f"ps:assertion:{content_digest(key)}"


__all__ = [
    "claim_node_assertion_id",
    "claim_node_content",
    "claim_node_context_id",
    "content_digest",
    "semantic_content",
]

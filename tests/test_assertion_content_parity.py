"""The claim content-projection schema has one spelling, projected twice.

``semantic_content`` (charter ``Claim``) and ``claim_node_content`` (graph
``ClaimNode``) must stay key-for-key identical, and ``content_digest`` must
keep producing the exact bytes persisted ``ps:assertion:`` ids are built from.
"""

from __future__ import annotations

import hashlib
import json

from propstore.core.assertions import (
    claim_node_content,
    content_digest,
    semantic_content,
)
from propstore.core.graph_types import ClaimNode
from propstore.core.id_types import to_claim_id, to_concept_id
from propstore.families.claims import Claim, ClaimType


def _charter_claim() -> Claim:
    return Claim(
        claim_id="ps:claim:parity:1",
        context_id="ps:context:parity",
        claim_type=ClaimType.PARAMETER,
        statement="speed of sound in air at 20C",
        name="speed_of_sound",
        output_concept="ps:concept:speed_of_sound",
        concepts=("ps:concept:speed_of_sound",),
        value=343.0,
        unit="m/s",
        confidence=0.9,
    )


def _lowered_node(claim: Claim) -> ClaimNode:
    content = semantic_content(claim)
    attributes = tuple(
        (key, value)
        for key, value in content.items()
        if key not in {"claim_type", "output_concept", "value"}
    )
    return ClaimNode(
        claim_id=to_claim_id(claim.claim_id),
        claim_type=ClaimType.PARAMETER,
        value_concept_id=(
            None
            if claim.output_concept is None
            else to_concept_id(claim.output_concept)
        ),
        scalar_value=claim.value,
        attributes=attributes,
    )


class TestContentProjectionParity:
    def test_key_schemas_are_identical(self) -> None:
        claim = _charter_claim()
        node = _lowered_node(claim)
        assert set(semantic_content(claim)) == set(claim_node_content(node))

    def test_projected_content_agrees_for_equivalent_inputs(self) -> None:
        claim = _charter_claim()
        node = _lowered_node(claim)
        claim_side = semantic_content(claim)
        node_side = claim_node_content(node)
        # concepts/equations lower as sequences; compare canonicalized.
        for key in claim_side:
            claim_value = claim_side[key]
            node_value = node_side[key]
            if isinstance(claim_value, (list, tuple)):
                claim_items: list[object] = [*claim_value]
                node_items: list[object] = (
                    [*node_value] if isinstance(node_value, (list, tuple)) else []
                )
                assert claim_items == node_items, key
            else:
                assert claim_value == node_value, key

    def test_content_digest_bytes_are_pinned(self) -> None:
        # Persisted ps:assertion: ids derive from exactly this encoding; a
        # change here is an identity migration, not a refactor.
        payload: dict[str, object] = {
            "content": {"value": 343.0, "unit": "m/s"},
            "conditions": [],
        }
        expected = hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), default=str
            ).encode("utf-8")
        ).hexdigest()
        assert content_digest(payload) == expected

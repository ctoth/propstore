from __future__ import annotations

from propstore.aspic import GroundAtom
from propstore.aspic_bridge import claims_to_literals
from propstore.core.literal_keys import (
    ClaimLiteralKey,
    GroundLiteralKey,
    claim_key,
    ground_key,
)


def test_claim_and_ground_literal_keys_are_disjoint_even_when_surface_matches() -> None:
    claim = claim_key("bird(tweety)")
    ground = ground_key(GroundAtom("bird", ("tweety",)), negated=False)

    assert claim != ground
    assert len({claim, ground}) == 2


def test_ground_literal_key_polarity_is_part_of_identity() -> None:
    atom = GroundAtom("p", (1,))

    positive = ground_key(atom, negated=False)
    negative = ground_key(atom, negated=True)

    assert positive != negative
    assert len({positive, negative}) == 2


def test_ground_literal_keys_hash_by_structure_not_instance_identity() -> None:
    left = ground_key(GroundAtom("edge", ("a", "b")), negated=False)
    right = ground_key(GroundAtom("edge", ("a", "b")), negated=False)

    assert left == right
    assert hash(left) == hash(right)


def test_claim_literal_key_preserves_claim_id() -> None:
    key = ClaimLiteralKey("claim-123")

    assert key.claim_id == "claim-123"
    assert key == claim_key("claim-123")


def test_ground_literal_key_preserves_atom_shape() -> None:
    key = GroundLiteralKey("reachable", ("src", 2, True), False)

    assert key == ground_key(
        GroundAtom("reachable", ("src", 2, True)),
        negated=False,
    )


def test_claims_to_literals_uses_typed_claim_keys() -> None:
    literals = claims_to_literals([
        {
            "id": "claim-typed",
            "concept_id": "concept-typed",
            "statement": "Typed claim",
            "premise_kind": "ordinary",
        }
    ])

    assert set(literals) == {claim_key("claim-typed")}

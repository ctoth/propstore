from __future__ import annotations

from propstore.aspic import GroundAtom
from propstore.aspic_bridge import (
    _literal_for_atom,
    _parse_ground_atom_key,
    claims_to_literals,
)


def _make_claim(claim_id: str) -> dict[str, object]:
    return {
        "id": claim_id,
        "concept_id": f"concept_{claim_id}",
        "statement": f"Claim {claim_id}",
        "premise_kind": "ordinary",
    }


def test_literal_for_atom_does_not_alias_opposite_polarities() -> None:
    literals: dict[str, object] = {}

    positive = _literal_for_atom(GroundAtom("p", (1,)), False, literals)  # type: ignore[arg-type]
    negative = _literal_for_atom(GroundAtom("p", (1,)), True, literals)  # type: ignore[arg-type]

    assert positive is not negative
    assert positive.negated is False
    assert negative.negated is True


def test_ground_literals_do_not_collide_with_claim_id_namespace() -> None:
    literals = claims_to_literals([_make_claim("bird(tweety)")])

    claim_literal = literals["bird(tweety)"]
    ground_literal = _literal_for_atom(
        GroundAtom("bird", ("tweety",)),
        False,
        literals,
    )

    assert claim_literal is not ground_literal
    assert claim_literal.atom.arguments == ()
    assert ground_literal.atom.arguments == ("tweety",)


def test_parse_ground_atom_key_round_trips_quoted_strings_and_numeric_scalars() -> None:
    parsed = _parse_ground_atom_key('p("a,b", 1, true, "1")')

    assert parsed == GroundAtom("p", ("a,b", 1, True, "1"))

from argumentation.aspic import conc

from propstore.aspic_bridge import build_bridge_csaf
from propstore.core.justifications import CanonicalJustification
from propstore.families.claims.declaration import Claim
from propstore.grounding.bundle import GroundedRulesBundle
from tests.typed_family_fixtures import claim_from_payload, stance_from_payload


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification.from_components(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _conclusion_claim_id(arg) -> str:
    literal = conc(arg)
    if literal.atom.predicate == "ist" and len(literal.atom.arguments) == 2:
        return str(literal.atom.arguments[1])
    return literal.atom.predicate


def test_undermines_is_preference_sensitive() -> None:
    claims = [
        _claim("claim:strong-target", confidence=0.9, sample_size=200),
        _claim("claim:weak-attacker", confidence=0.1, sample_size=1),
    ]
    justifications = [
        _reported("claim:strong-target"),
        _reported("claim:weak-attacker"),
    ]
    stances = [
        stance_from_payload(
            {
                "claim_id": "claim:weak-attacker",
                "target_claim_id": "claim:strong-target",
                "stance_type": "undermines",
            }
        )
    ]

    csaf = build_bridge_csaf(
        claims,
        justifications,
        stances,
        bundle=GroundedRulesBundle.empty(),
    )

    attacker_ids = {
        csaf.arg_to_id[arg]
        for arg in csaf.arguments
        if _conclusion_claim_id(arg) == "claim:weak-attacker"
    }
    target_ids = {
        csaf.arg_to_id[arg]
        for arg in csaf.arguments
        if _conclusion_claim_id(arg) == "claim:strong-target"
    }
    undermining_edges = {
        (attacker_id, target_id)
        for attacker_id in attacker_ids
        for target_id in target_ids
    }

    assert undermining_edges
    assert undermining_edges.isdisjoint(csaf.framework.defeats)

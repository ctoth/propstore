import pytest

from argumentation.aspic import Attack, GroundAtom, Literal, PremiseArg
from propstore.aspic_bridge import build
from propstore.core.justifications import CanonicalJustification
from propstore.grounding.bundle import GroundedRulesBundle


def test_build_bridge_csaf_rejects_attack_outside_argument_domain(monkeypatch) -> None:
    outside = PremiseArg(
        Literal(GroundAtom("outside_bridge_argument_domain")),
        is_axiom=False,
    )

    def compute_attacks_with_outside_argument(arguments, system):
        inside = next(iter(arguments))
        return frozenset({Attack(outside, inside, inside, "rebutting")})

    monkeypatch.setattr(build, "compute_attacks", compute_attacks_with_outside_argument)
    monkeypatch.setattr(build, "compute_defeats", lambda *args, **kwargs: frozenset())

    with pytest.raises((AssertionError, KeyError), match="argument domain|outside"):
        build.build_bridge_csaf(
            [
                {
                    "id": "claim-a",
                    "concept_id": "concept-a",
                    "premise_kind": "ordinary",
                }
            ],
            [
                CanonicalJustification(
                    justification_id="reported:claim-a",
                    conclusion_claim_id="claim-a",
                    premise_claim_ids=(),
                    rule_kind="reported_claim",
                )
            ],
            [],
            bundle=GroundedRulesBundle.empty(),
        )

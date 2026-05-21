import pytest

from propstore.aspic_bridge import claims_to_literals, justifications_to_rules
from propstore.core.justifications import CanonicalJustification
from tests.typed_family_fixtures import claim_from_payload


def test_justifications_to_rules_rejects_unknown_premise() -> None:
    literals = claims_to_literals(
        [
            claim_from_payload(
                {
                    "id": "conclusion",
                    "concept_id": "concept-conclusion",
                    "premise_kind": "ordinary",
                }
            )
        ]
    )

    with pytest.raises(ValueError, match="unknown premise.*missing-premise"):
        justifications_to_rules(
            [
                CanonicalJustification(
                    justification_id="support:missing->conclusion",
                    conclusion_claim_id="conclusion",
                    premise_claim_ids=("missing-premise",),
                    rule_kind="support",
                    rule_strength="defeasible",
                )
            ],
            literals,
        )

from __future__ import annotations

from eq_equiv import equation_signature

from propstore.conflict_detector.equation_inputs import bound_equation_from_conflict_claim
from propstore.conflict_detector.models import ConflictClaim, ConflictClaimVariable


def test_equation_signature_ignores_author_dependent_role_choice() -> None:
    first = ConflictClaim(
        claim_id="a",
        claim_type="equation",
        expression="F = m * a",
        variables=(
            ConflictClaimVariable(concept_id="force", symbol="F", role="dependent"),
            ConflictClaimVariable(concept_id="mass", symbol="m", role="independent"),
            ConflictClaimVariable(concept_id="acceleration", symbol="a", role="independent"),
        ),
    )
    second = ConflictClaim(
        claim_id="b",
        claim_type="equation",
        expression="F = m * a",
        variables=(
            ConflictClaimVariable(concept_id="force", symbol="F", role="independent"),
            ConflictClaimVariable(concept_id="mass", symbol="m", role="dependent"),
            ConflictClaimVariable(concept_id="acceleration", symbol="a", role="independent"),
        ),
    )

    assert equation_signature(
        bound_equation_from_conflict_claim(first)
    ) == equation_signature(
        bound_equation_from_conflict_claim(second)
    )

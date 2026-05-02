from __future__ import annotations

import json

import pytest

from propstore.core.active_claims import ActiveClaim
from propstore.core.activation import UnknownConceptInCEL, is_active_claim_active
from propstore.core.environment import Environment
from propstore.core.conditions.solver import ConditionSolver


def test_unknown_cel_identifier_raises_with_context() -> None:
    claim = ActiveClaim.from_mapping(
        {
            "id": "claim-01",
            "artifact_id": "test-01",
            "conditions_cel": json.dumps(["some_unknown_concept > 5"]),
        }
    )

    with pytest.raises(UnknownConceptInCEL) as ei:
        is_active_claim_active(
            claim,
            environment=Environment(bindings={"framework": "general"}),
            solver=ConditionSolver({}),
        )

    assert "some_unknown_concept" in str(ei.value)
    assert "test-01" in str(ei.value)

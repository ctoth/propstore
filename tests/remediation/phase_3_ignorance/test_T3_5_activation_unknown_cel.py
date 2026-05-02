from __future__ import annotations

import json

import pytest

from propstore.core.active_claims import ActiveClaim
from propstore.core.activation import UnknownConceptInCEL, is_active_claim_active
from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.environment import Environment
from propstore.core.conditions.solver import ConditionSolver


def test_unknown_cel_identifier_raises_with_context() -> None:
    checked_registry = {
        "some_unknown_concept": ConceptInfo(
            id="some_unknown_concept",
            canonical_name="some_unknown_concept",
            kind=KindType.QUANTITY,
        )
    }
    condition = "some_unknown_concept > 5"
    claim = ActiveClaim.from_mapping(
        {
            "id": "claim-01",
            "artifact_id": "test-01",
            "conditions_cel": json.dumps([condition]),
            "conditions_ir": json.dumps(
                checked_condition_set_to_json(
                    checked_condition_set(
                        [check_condition_ir(condition, checked_registry)]
                    )
                ),
                sort_keys=True,
            ),
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

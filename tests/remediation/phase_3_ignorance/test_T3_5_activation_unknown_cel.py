from __future__ import annotations

import pytest

from propstore.core.activation import UnknownConceptInCEL, is_claim_active
from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
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
    claim_conditions = checked_condition_set(
        [check_condition_ir(condition, checked_registry)]
    )

    with pytest.raises(UnknownConceptInCEL) as ei:
        is_claim_active(
            claim_id="claim-01",
            claim_context_id=None,
            claim_conditions=claim_conditions,
            source_artifact="test-01",
            environment=Environment(bindings={"framework": "general"}),
            solver=ConditionSolver({}),
        )

    assert "some_unknown_concept" in str(ei.value)
    assert "test-01" in str(ei.value)

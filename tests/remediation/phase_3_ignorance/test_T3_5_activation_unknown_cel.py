from __future__ import annotations

import pytest

from propstore.core.activation import is_claim_active
from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
)
from propstore.core.conditions.registry import ConditionRegistry, ConceptInfo, KindType
from propstore.core.environment import Environment
from propstore.core.conditions.solver import ConditionSolver
from propstore.core.conditions.solver import Z3TranslationError


def test_inferable_runtime_cel_identifier_is_local_to_environment_scope() -> None:
    checked_registry = ConditionRegistry(
        {
            "known_concept": ConceptInfo(
                id="known_concept",
                canonical_name="known_concept",
                kind=KindType.QUANTITY,
            )
        }
    )
    condition = "known_concept > 5"
    claim_conditions = checked_condition_set(
        [check_condition_ir(condition, checked_registry)]
    )

    assert (
        is_claim_active(
            claim_id="claim-01",
            claim_context_id=None,
            claim_conditions=claim_conditions,
            source_artifact="test-01",
            environment=Environment(
                effective_assumptions=("some_unknown_concept > 5",),
            ),
            solver=ConditionSolver(checked_registry),
        )
        is True
    )


def test_claim_condition_registry_mismatch_surfaces_solver_contract() -> None:
    checked_registry = ConditionRegistry(
        {
            "some_unknown_concept": ConceptInfo(
                id="some_unknown_concept",
                canonical_name="some_unknown_concept",
                kind=KindType.QUANTITY,
            )
        }
    )
    condition = "some_unknown_concept > 5"
    claim_conditions = checked_condition_set(
        [check_condition_ir(condition, checked_registry)]
    )

    with pytest.raises(Z3TranslationError, match="different condition registry"):
        is_claim_active(
            claim_id="claim-01",
            claim_context_id=None,
            claim_conditions=claim_conditions,
            source_artifact="test-01",
            environment=Environment(bindings={"framework": "general"}),
            solver=ConditionSolver(ConditionRegistry()),
        )

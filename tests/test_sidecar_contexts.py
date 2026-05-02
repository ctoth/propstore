from __future__ import annotations

import json

from propstore.context_lifting import (
    IstProposition,
    LiftingDecisionStatus,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.sidecar.passes import compile_context_lifting_materialization_rows
from propstore.core.conditions.registry import ConceptInfo, KindType
from propstore.core.conditions.solver import SolverSat, SolverUnknown, SolverUnknownReason


class _ConditionSolver:
    def __init__(self, result):
        self._registry = {
            "license": ConceptInfo(
                id="license",
                canonical_name="license",
                kind=KindType.CATEGORY,
                category_values=["bridge", "open"],
                category_extensible=True,
            )
        }
        self.result = result

    def is_condition_satisfied_result(self, condition, bindings):
        return self.result


def _system(condition: str) -> LiftingSystem:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    return LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(
                id="lift-source-target",
                source=source,
                target=target,
                conditions=(condition,),
            ),
        ),
    )


def test_sidecar_materialization_rows_persist_decision_status_and_witness_reference() -> None:
    assertion = IstProposition(
        context=ContextReference("ctx_source"),
        proposition_id="claim_alpha",
    )
    decisions = _system("license == 'bridge'").lift_decisions_for(
        assertion,
        solver=_ConditionSolver(SolverUnknown(SolverUnknownReason.TIMEOUT, "timeout")),
        bindings={"license": "bridge"},
    )

    row = compile_context_lifting_materialization_rows(decisions)[0]
    values = row.values
    provenance = json.loads(values[6])

    assert values[4] == LiftingDecisionStatus.UNKNOWN.value
    assert provenance["status"] == "unknown"
    assert provenance["diagnostic"] == "lifting rule condition is unknown: timeout"


def test_sidecar_materialization_rows_are_recomputed_inspection_records() -> None:
    assertion = IstProposition(
        context=ContextReference("ctx_source"),
        proposition_id="claim_alpha",
    )
    old_row = compile_context_lifting_materialization_rows(
        _system("license == 'bridge'").lift_decisions_for(
            assertion,
            solver=_ConditionSolver(
                SolverUnknown(SolverUnknownReason.TIMEOUT, "timeout")
            ),
            bindings={"license": "bridge"},
        )
    )[0]
    new_row = compile_context_lifting_materialization_rows(
        _system("license == 'open'").lift_decisions_for(
            assertion,
            solver=_ConditionSolver(SolverSat()),
            bindings={"license": "open"},
        )
    )[0]

    assert old_row.values[4] == "unknown"
    assert new_row.values[4] == "lifted"
    assert old_row.values[6] != new_row.values[6]

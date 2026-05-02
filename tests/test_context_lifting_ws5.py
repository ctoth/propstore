from __future__ import annotations

import json
import sqlite3

from propstore.context_lifting import (
    IstProposition,
    LiftingException,
    LiftingDecisionStatus,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.families.contexts.stages import LoadedContext
from propstore.sidecar.passes import (
    compile_context_lifting_materialization_rows,
    compile_context_sidecar_rows,
)
from propstore.sidecar.schema import create_context_tables, populate_contexts
from propstore.sidecar.stages import ContextSidecarRows
from propstore.world.bound import BoundWorld
from propstore.world.types import Environment
from propstore.core.conditions.solver import (
    ConditionSolver,
    SolverSat,
    SolverUnknown,
    SolverUnknownReason,
    SolverUnsat,
    Z3TranslationError,
)


class _ConditionSolver:
    def __init__(self, result):
        self.result = result

    def is_condition_satisfied_result(self, condition, bindings):
        result = self.result
        if isinstance(result, Exception):
            raise result
        return result


def test_lifting_materializes_ist_assertion_with_rule_provenance() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(
                id="lift-source-target",
                source=source,
                target=target,
                justification="Guha DCR-T bridge",
            ),
        ),
    )

    materializations = system.materialize_lifted_assertions(
        (IstProposition(context=source, proposition_id="claim_alpha"),)
    )

    assert len(materializations) == 1
    lifted = materializations[0]
    assert lifted.status is LiftingDecisionStatus.LIFTED
    assert lifted.assertion == IstProposition(
        context=target,
        proposition_id="claim_alpha",
    )
    assert lifted.source_assertion == IstProposition(
        context=source,
        proposition_id="claim_alpha",
    )
    assert lifted.rule_id == "lift-source-target"
    assert lifted.provenance.items() >= {
        "rule_id": "lift-source-target",
        "source_context_id": "ctx_source",
        "target_context_id": "ctx_target",
        "source_proposition_id": "claim_alpha",
        "status": "lifted",
    }.items()
    assert lifted.provenance["justification"] == "Guha DCR-T bridge"


def test_lifting_exception_is_local_and_blocks_only_matching_target() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    sibling = ContextReference("ctx_sibling")
    system = LiftingSystem(
        contexts=(source, target, sibling),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
            LiftingRule(id="lift-source-sibling", source=source, target=sibling),
        ),
        lifting_exceptions=(
            LiftingException(
                id="except-target-alpha",
                rule_id="lift-source-target",
                target=target,
                proposition_id="claim_alpha",
                clashing_set=("ctx_target:claim_beta",),
                justification="local target clashing set",
            ),
        ),
    )

    assertion = IstProposition(context=source, proposition_id="claim_alpha")
    decisions = system.lift_decisions_for(assertion)

    by_target = {str(item.target_context.id): item for item in decisions}
    assert by_target["ctx_target"].status is LiftingDecisionStatus.BLOCKED
    assert by_target["ctx_target"].provenance.exception_id == "except-target-alpha"
    assert by_target["ctx_sibling"].status is LiftingDecisionStatus.LIFTED
    assert {
        str(item.target_context.id)
        for item in system.materialize_lifted_assertions((assertion,))
    } == {"ctx_sibling"}


def test_lifting_rule_conditions_are_decision_gates() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(
                id="lift-source-target",
                source=source,
                target=target,
                conditions=("license == 'bridge'",),
            ),
        ),
    )
    assertion = IstProposition(context=source, proposition_id="claim_alpha")

    lifted = system.lift_decisions_for(
        assertion,
        solver=_ConditionSolver(SolverSat()),
        bindings={"license": "bridge"},
    )[0]
    blocked = system.lift_decisions_for(
        assertion,
        solver=_ConditionSolver(SolverUnsat()),
        bindings={"license": "closed"},
    )[0]
    unknown = system.lift_decisions_for(
        assertion,
        solver=_ConditionSolver(SolverUnknown(SolverUnknownReason.TIMEOUT, "timeout")),
        bindings={"license": "bridge"},
    )[0]
    authoring_unbound = system.lift_decisions_for(
        assertion,
        solver=_ConditionSolver(Z3TranslationError("unknown concept")),
        bindings={},
    )[0]

    assert lifted.status is LiftingDecisionStatus.LIFTED
    assert blocked.status is LiftingDecisionStatus.BLOCKED
    assert unknown.status is LiftingDecisionStatus.UNKNOWN
    assert authoring_unbound.status is LiftingDecisionStatus.UNKNOWN
    assert unknown.solver_witness is not None
    assert authoring_unbound.provenance.diagnostic is not None


def test_lifting_system_does_not_expose_visibility_as_semantics() -> None:
    system = LiftingSystem(contexts=(ContextReference("ctx_target"),))

    assert not hasattr(system, "contexts_visible_from")


def test_bound_world_projection_honors_local_lifting_exception() -> None:
    class _Store:
        def __init__(self) -> None:
            self._solver = ConditionSolver({})
            self._claims = [
                {"id": "claim_alpha", "concept_id": "c1", "context_id": "ctx_source"},
                {"id": "claim_local", "concept_id": "c1", "context_id": "ctx_target"},
            ]

        def claims_for(self, concept_id):
            return [
                claim
                for claim in self._claims
                if concept_id is None or claim.get("concept_id") == concept_id
            ]

        def condition_solver(self):
            return self._solver

    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
        ),
        lifting_exceptions=(
            LiftingException(
                id="except-alpha",
                rule_id="lift-source-target",
                target=target,
                proposition_id="claim_alpha",
                clashing_set=("ctx_target:claim_local",),
                justification="target-local undercutter",
            ),
        ),
    )

    bound = BoundWorld(
        _Store(),
        environment=Environment(context_id="ctx_target"),
        lifting_system=system,
    )

    assert {str(claim.claim_id) for claim in bound.active_claims("c1")} == {
        "claim_local",
    }


def test_sidecar_stores_lifting_materialization_provenance() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_context_tables(conn)

    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
        ),
    )
    materializations = system.materialize_lifted_assertions(
        (IstProposition(context=source, proposition_id="claim_alpha"),)
    )
    materialization_rows = compile_context_lifting_materialization_rows(
        materializations
    )

    populate_contexts(
        conn,
        ContextSidecarRows(
            context_rows=(),
            assumption_rows=(),
            lifting_rule_rows=(),
            lifting_materialization_rows=materialization_rows,
        ),
    )

    row = conn.execute(
        "SELECT * FROM context_lifting_materialization"
    ).fetchone()
    assert row["rule_id"] == "lift-source-target"
    assert row["source_context_id"] == "ctx_source"
    assert row["target_context_id"] == "ctx_target"
    assert row["proposition_id"] == "claim_alpha"
    assert row["status"] == "lifted"
    assert json.loads(row["provenance_json"])["source_proposition_id"] == "claim_alpha"


def test_context_sidecar_compiler_materializes_authored_ist_assertions() -> None:
    rows = compile_context_sidecar_rows(
        (
            LoadedContext.from_payload(
                filename="source.yaml",
                source_path=None,
                data={"id": "ctx_source", "name": "Source"},
            ),
            LoadedContext.from_payload(
                filename="target.yaml",
                source_path=None,
                data={
                    "id": "ctx_target",
                    "name": "Target",
                    "lifting_rules": [
                        {
                            "id": "lift-source-target",
                            "source": "ctx_source",
                            "target": "ctx_target",
                        },
                    ],
                },
            ),
        ),
        authored_ist_assertions=(
            IstProposition(
                context=ContextReference("ctx_source"),
                proposition_id="claim_alpha",
            ),
        ),
    )

    assert len(rows.lifting_materialization_rows) == 1
    assert rows.lifting_materialization_rows[0].values[:5] == (
        "lift-source-target",
        "ctx_source",
        "ctx_target",
        "claim_alpha",
        "lifted",
    )

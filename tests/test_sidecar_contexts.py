"""Phase 4 sidecar projection of lifting decisions (non-commitment).

A lifting decision of ANY status is projected into the
``lifting_materialization`` sidecar with its full provenance columns. An UNKNOWN
decision and a later LIFTED decision for the same lift coexist as distinct rows —
storage records the actual decision; render decides what is visible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from condition_ir import (
    CheckedCondition,
    ConceptInfo,
    ConditionSolver,
    KindType,
    SolverResult,
    SolverUnknown,
    SolverUnknownReason,
)

import propstore.claim_conditions as cc
from propstore.context_lifting import LiftingSystem
from propstore.defeasibility import CelScalar
from propstore.families.contexts import (
    Context,
    ContextRepository,
    LiftingDecisionStatus,
    LiftingRule,
)


@dataclass(frozen=True)
class _TimeoutSolver:
    inner: ConditionSolver

    @property
    def registry(self) -> Mapping[str, ConceptInfo]:
        return self.inner.registry

    def is_condition_satisfied_result(
        self, condition: CheckedCondition, bindings: Mapping[str, CelScalar]
    ) -> SolverResult:
        return SolverUnknown(SolverUnknownReason.TIMEOUT, "timeout")


def _solver() -> ConditionSolver:
    registry = cc.condition_registry(
        [
            ConceptInfo(
                id="task",
                canonical_name="task",
                kind=KindType.CATEGORY,
                category_values=["speech", "text"],
                category_extensible=True,
            )
        ]
    )
    return ConditionSolver(registry)


def _system() -> LiftingSystem:
    src = Context(context_id="ctx_src", name="src")
    tgt = Context(context_id="ctx_tgt", name="tgt")
    rule = LiftingRule(
        rule_id="r",
        source_context="ctx_src",
        target_context="ctx_tgt",
        conditions=('task == "speech"',),
    )
    return LiftingSystem(contexts=(src, tgt), lifting_rules=(rule,))


def test_unknown_decision_is_projected_with_diagnostic(tmp_path: Path) -> None:
    system = _system()
    decisions = system.lift_decisions_between(
        "ctx_src", "ctx_tgt", "p", solver=_TimeoutSolver(_solver())
    )
    repo = ContextRepository()
    repo.author(Context(context_id="ctx_src", name="src"), message="m")
    repo.author(Context(context_id="ctx_tgt", name="tgt"), message="m")
    schema = repo.build_sidecar(tmp_path / "side.db", lifting_decisions=decisions)
    rows = repo.render_materializations(tmp_path / "side.db", schema)
    assert len(rows) == 1
    (row,) = rows
    assert row.status is LiftingDecisionStatus.UNKNOWN
    assert row.diagnostic == "lifting rule condition is unknown: timeout"


def test_unknown_and_lifted_decisions_coexist_as_distinct_rows(tmp_path: Path) -> None:
    system = _system()
    unknown = system.lift_decisions_between(
        "ctx_src", "ctx_tgt", "p", solver=_TimeoutSolver(_solver())
    )
    lifted = system.lift_decisions_between(
        "ctx_src", "ctx_tgt", "p", solver=_solver(), bindings={"task": "speech"}
    )
    assert [d.status for d in lifted] == [LiftingDecisionStatus.LIFTED]
    repo = ContextRepository()
    repo.author(Context(context_id="ctx_src", name="src"), message="m")
    repo.author(Context(context_id="ctx_tgt", name="tgt"), message="m")
    schema = repo.build_sidecar(
        tmp_path / "side.db", lifting_decisions=unknown + lifted
    )
    rows = repo.render_materializations(tmp_path / "side.db", schema)
    statuses = sorted(row.status.value for row in rows)
    assert statuses == ["lifted", "unknown"]
    assert len({row.materialization_id for row in rows}) == 2

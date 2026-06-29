"""Phase 4 lifting-rule decision algebra (McCarthy/Guha, no ancestry).

The reference exercised these through ist-proposition documents and a worldline;
the rewrite exercises the same behavioral contract directly on the lifting
algebra: an authored gate with no solver is UNKNOWN, lifts are directional, and a
non-LIFTED decision never materializes an assertion.
"""

from __future__ import annotations

import msgspec
import pytest

from propstore.context_lifting import IstProposition, LiftingSystem
from propstore.families.contexts import Context, LiftingDecisionStatus, LiftingRule


def _system() -> LiftingSystem:
    source = Context(context_id="ctx_source", name="source")
    target = Context(context_id="ctx_target", name="target")
    rule = LiftingRule(
        rule_id="lift",
        source_context="ctx_source",
        target_context="ctx_target",
        conditions=("task == 'speech'",),
    )
    return LiftingSystem(contexts=(source, target), lifting_rules=(rule,))


@pytest.mark.parametrize("banned", ["inherits", "excludes"])
def test_context_document_rejects_inherits_and_excludes(banned: str) -> None:
    with pytest.raises(msgspec.ValidationError, match=banned):
        msgspec.convert({"context_id": "c", "name": "n", banned: ["x"]}, Context)


def test_gate_without_solver_is_unknown() -> None:
    system = _system()
    decisions = system.lift_decisions_between("ctx_source", "ctx_target", "claim_source")
    assert [d.status for d in decisions] == [LiftingDecisionStatus.UNKNOWN]


def test_lifting_is_directional() -> None:
    system = _system()
    assert system.lift_decisions_between("ctx_target", "ctx_source", "claim_source") == ()


def test_unknown_decision_does_not_materialize() -> None:
    system = _system()
    assert (
        system.materialize_lifted_assertions(
            (IstProposition("ctx_source", "claim_source"),)
        )
        == ()
    )


def test_effective_assumptions_are_target_local() -> None:
    system = _system()
    assert system.effective_assumptions("ctx_target") == ()

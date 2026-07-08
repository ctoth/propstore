"""Bozzato 2018 justified exceptions at the lifting/ASPIC+ boundary.

An authored :class:`LiftingException` must not act as a projection-time gate.
Per Bozzato 2018 (Def 12, p.15): an exception overrides only when its clashing
set is *established* — there is actual local evidence. So an exception-affected
lift is ``EXCEPTED``: its defeasible rule still reaches the argumentation
framework, and the exception contributes Dung defeats only from arguments that
conclude the clashing-set claims. No clashing argument → no override → the
lifted assertion survives.
"""

from __future__ import annotations

import warnings

import pytest
from argumentation.structured.aspic.aspic import Argument, conc

from propstore.aspic_bridge import build_bridge_csaf, project_lifting_decisions
from propstore.context_lifting import (
    Context,
    LiftingException,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.justifications import CanonicalJustification
from propstore.families.contexts import LiftingDecisionStatus
from propstore.grounding.bundle import GroundedRulesBundle


def _claim(claim_id: str, context_id: str) -> dict[str, object]:
    return {
        "id": claim_id,
        "concept_id": "k",
        "statement": claim_id,
        "premise_kind": "ordinary",
        "context_id": context_id,
    }


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _excepted_decision():
    system = LiftingSystem(
        contexts=(
            Context(context_id="ctx:src", name="src"),
            Context(context_id="ctx:tgt", name="tgt"),
        ),
        lifting_rules=(
            LiftingRule(
                rule_id="lift:src-tgt",
                source_context="ctx:src",
                target_context="ctx:tgt",
            ),
        ),
        lifting_exceptions=(
            LiftingException(
                id="except:one",
                rule_id="lift:src-tgt",
                target="ctx:tgt",
                proposition_id="claim:p",
                clashing_set=("claim:q",),
                justification="local clash",
            ),
        ),
    )
    (decision,) = system.lift_decisions_between("ctx:src", "ctx:tgt", "claim:p")
    return decision


def _concludes_ist(argument: Argument, context_id: str, claim_id: str) -> bool:
    atom = conc(argument).atom
    return atom.predicate == "ist" and atom.arguments == (context_id, claim_id)


def _concludes_claim(argument: Argument, claim_id: str) -> bool:
    atom = conc(argument).atom
    if atom.predicate == claim_id:
        return True
    return atom.predicate == "ist" and atom.arguments[-1:] == (claim_id,)


class TestExceptedDecisionStatus:
    def test_exception_yields_excepted_not_blocked(self) -> None:
        decision = _excepted_decision()
        assert decision.status is LiftingDecisionStatus.EXCEPTED
        assert decision.exception_id == "except:one"
        assert decision.clashing_set == ("claim:q",)
        assert decision.exception is not None


class TestExceptedProjection:
    def test_excepted_lift_still_emits_a_defeasible_rule(self) -> None:
        decision = _excepted_decision()
        projection = project_lifting_decisions({}, [decision])
        assert any(rule.name == "lift:src-tgt" for rule in projection.defeasible_rules)
        assert not projection.strict_rules


class TestBozzatoJustification:
    def test_established_clashing_set_defeats_the_lifted_assertion(self) -> None:
        decision = _excepted_decision()
        csaf = build_bridge_csaf(
            [_claim("claim:p", "ctx:src"), _claim("claim:q", "ctx:tgt")],
            [_reported("claim:p"), _reported("claim:q")],
            [],
            bundle=GroundedRulesBundle.empty(),
            lifting_decisions=[decision],
        )
        lifted = {
            argument
            for argument in csaf.arguments
            if _concludes_ist(argument, "ctx:tgt", "claim:p")
        }
        clashing = {
            argument
            for argument in csaf.arguments
            if _concludes_claim(argument, "claim:q")
        }
        assert lifted, "the excepted lift's rule must still build an argument"
        assert clashing
        assert any(
            (attacker, target) in csaf.defeats
            for attacker in clashing
            for target in lifted
        ), "an established clashing set must defeat the lifted assertion"

    def test_unestablished_clashing_set_does_not_override(self) -> None:
        decision = _excepted_decision()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            csaf = build_bridge_csaf(
                [_claim("claim:p", "ctx:src")],
                [_reported("claim:p")],
                [],
                bundle=GroundedRulesBundle.empty(),
                lifting_decisions=[decision],
            )
        lifted = {
            argument
            for argument in csaf.arguments
            if _concludes_ist(argument, "ctx:tgt", "claim:p")
        }
        assert lifted, "an unjustified exception must not suppress the lift"
        assert not any(target in lifted for _, target in csaf.defeats), (
            "no clashing argument exists, so nothing may defeat the lifted assertion"
        )
        assert any("clashing" in str(warning.message) for warning in caught), (
            "the unjustified exception must be surfaced, not silently ignored"
        )

    def test_gate_blocked_lift_still_emits_no_rule(self) -> None:
        decision = _excepted_decision()
        blocked = type(decision)(
            rule_id=decision.rule_id,
            proposition_id=decision.proposition_id,
            source_context=decision.source_context,
            target_context=decision.target_context,
            status=LiftingDecisionStatus.BLOCKED,
            mode=decision.mode,
            support=decision.support,
            diagnostic="gate unsatisfiable",
        )
        projection = project_lifting_decisions({}, [blocked])
        assert not projection.defeasible_rules
        assert not projection.strict_rules


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

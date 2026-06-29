"""CKR justifiable exceptions inject Dung defeats into a CSAF.

ASPIC+ builds the structural arguments; propstore decides contextual
applicability and, for an excepted contextual claim, adds a defeat from every
argument concluding the exception's justification claim onto every argument
concluding the excepted claim. ASPIC+ never owns the contextual exception
semantics (CLAUDE.md); the defeat is injected at the Dung boundary via the
package's CSAF.
"""

from __future__ import annotations

from argumentation.core.dung import complete_extensions, conflict_free, grounded_extension
from argumentation.structured.aspic.aspic import Argument, conc
from provenance_semiring import (
    ProvenancePolynomial,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
)

from propstore.aspic_bridge import build_bridge_csaf
from propstore.core.justifications import CanonicalJustification
from propstore.defeasibility import (
    ClaimApplicability,
    ContextualClaimUse,
    DecidabilityStatus,
    JustifiableException,
    apply_exception_defeats_to_csaf,
    evaluate_contextual_claim,
)
from propstore.grounding.bundle import GroundedRulesBundle


def _claim(claim_id: str) -> dict[str, object]:
    return {"id": claim_id, "concept_id": "k", "statement": claim_id, "premise_kind": "ordinary"}


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _csaf() -> object:
    return build_bridge_csaf(
        [_claim("claim:target"), _claim("claim:exception-justification")],
        [_reported("claim:target"), _reported("claim:exception-justification")],
        [],
        bundle=GroundedRulesBundle.empty(),
    )


def _exception() -> JustifiableException:
    return JustifiableException(
        target_claim="claim:target",
        exception_pattern="true",
        justification_claims=("claim:exception-justification",),
        context="ctx:trial",
        support=SupportEvidence(
            ProvenancePolynomial.variable(SourceVariableId("ps:source:exception")),
            SupportQuality.EXACT,
        ),
        decidability_status=DecidabilityStatus.DECIDABLE,
    )


def _result() -> object:
    return evaluate_contextual_claim(
        ContextualClaimUse("ctx:trial", "claim:target"), (_exception(),)
    )


def _ids_concluding(csaf, claim_id: str) -> set[str]:
    return {
        csaf.arg_to_id[argument]
        for argument in csaf.arguments
        if _concludes(argument, claim_id)
    }


def _concludes(argument: Argument, claim_id: str) -> bool:
    atom = conc(argument).atom
    return atom.predicate == "ist" and atom.arguments[-1:] == (claim_id,)


def test_exception_defeat_adds_justification_argument_defeat_to_csaf() -> None:
    csaf = _csaf()
    result = _result()
    assert result.applicability is ClaimApplicability.EXCEPTED
    integrated = apply_exception_defeats_to_csaf(csaf, [result])

    attacker_ids = _ids_concluding(integrated, "claim:exception-justification")
    target_ids = _ids_concluding(integrated, "claim:target")
    assert attacker_ids
    assert target_ids
    assert any(
        (attacker_id, target_id) in integrated.framework.defeats
        for attacker_id in attacker_ids
        for target_id in target_ids
    )


def test_exception_defeat_participates_in_dung_extension() -> None:
    integrated = apply_exception_defeats_to_csaf(_csaf(), [_result()])
    grounded = grounded_extension(integrated.framework)
    attacker_ids = _ids_concluding(integrated, "claim:exception-justification")
    target_ids = _ids_concluding(integrated, "claim:target")
    assert attacker_ids <= grounded
    assert target_ids.isdisjoint(grounded)


def test_exception_augmented_framework_remains_attack_conflict_free() -> None:
    integrated = apply_exception_defeats_to_csaf(_csaf(), [_result()])
    assert integrated.framework.attacks is not None
    for extension in complete_extensions(integrated.framework):
        assert conflict_free(extension, integrated.framework.attacks)

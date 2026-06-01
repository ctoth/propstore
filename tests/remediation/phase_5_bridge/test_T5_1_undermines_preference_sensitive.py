from argumentation.aspic import conc

from propstore.core.justifications import CanonicalJustification


def _reported(claim_id: str) -> CanonicalJustification:
    return CanonicalJustification.from_components(
        justification_id=f"reported:{claim_id}",
        conclusion_claim_id=claim_id,
        rule_kind="reported_claim",
    )


def _conclusion_claim_id(arg) -> str:
    literal = conc(arg)
    if literal.atom.predicate == "ist" and len(literal.atom.arguments) == 2:
        return str(literal.atom.arguments[1])
    return literal.atom.predicate

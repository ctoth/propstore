from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from propstore.core.justifications import CanonicalJustification
from propstore.grounding.bundle import GroundedRulesBundle


def _claim(claim_id: str) -> dict[str, object]:
    return {
        "id": claim_id,
        "concept_id": f"concept_{claim_id}",
        "premise_kind": "ordinary",
    }


def _justification(
    justification_id: str,
    conclusion_claim_id: str,
    premise_claim_ids: tuple[str, ...] = (),
    *,
    rule_kind: str = "reported_claim",
) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=conclusion_claim_id,
        premise_claim_ids=premise_claim_ids,
        rule_kind=rule_kind,
        rule_strength="defeasible",
    )


def test_chained_projection_separates_direct_premises_from_recursive_dependencies() -> None:
    claims = [_claim("A"), _claim("B"), _claim("C")]
    justifications = [
        _justification("reported:A", "A"),
        _justification("reported:B", "B"),
        _justification("reported:C", "C"),
        _justification("supports:A->B", "B", ("A",), rule_kind="supports"),
        _justification("supports:B->C", "C", ("B",), rule_kind="supports"),
    ]
    csaf = build_bridge_csaf(
        claims,
        justifications,
        [],
        bundle=GroundedRulesBundle.empty(),
    )

    projection = csaf_to_projection(csaf, claims)
    by_id = {argument.arg_id: argument for argument in projection.arguments}
    chained_c_arguments = [
        argument
        for argument in projection.arguments
        if argument.claim_id == "C"
        and argument.justification_id == "supports:B->C"
        and any(
            by_id[subargument_id].claim_id == "B"
            and by_id[subargument_id].justification_id == "supports:A->B"
            for subargument_id in argument.subargument_ids
        )
    ]

    assert chained_c_arguments
    chained = chained_c_arguments[0]
    assert chained.premise_claim_ids == ("B",)
    assert chained.dependency_claim_ids == ("A",)
    assert chained.premise_claim_ids != chained.dependency_claim_ids

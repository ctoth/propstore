from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from tests.test_aspic_bridge_review_v2 import (
    _make_atom,
    _make_grounded_bundle,
    _make_rule_document,
    _make_var,
)


def test_grounded_predicate_does_not_project_as_same_named_claim() -> None:
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("fly", (_make_var("X"),)),
                (_make_atom("bird", (_make_var("X"),)),),
            ),
        ),
        definitely={"bird": {("tweety",)}},
    )
    csaf = build_bridge_csaf([], [], [], bundle=bundle)

    projection = csaf_to_projection(
        csaf,
        [
            {
                "id": "fly",
                "concept_id": "concept-fly",
                "premise_kind": "ordinary",
            }
        ],
    )

    grounded_fly_args = [
        argument
        for argument in projection.arguments
        if '"predicate":"fly"' in argument.conclusion_key
        and '"arguments":[{"type":"str","value":"tweety"}]' in argument.conclusion_key
    ]

    assert grounded_fly_args
    assert all(argument.claim_id is None for argument in grounded_fly_args)
    assert projection.claim_to_argument_ids == {}
    assert projection.argument_to_claim_id == {}

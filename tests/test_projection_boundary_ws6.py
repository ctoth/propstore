from __future__ import annotations

from argumentation.aspic import GroundAtom

from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from propstore.core.justifications import CanonicalJustification
from propstore.structured_projection import ProjectionAtom, ProjectionLossWitness
from tests.test_aspic_bridge_review_v2 import (
    _make_atom,
    _make_grounded_bundle,
    _make_rule_document,
    _make_var,
)


def test_aspic_projection_arguments_expose_typed_source_projection_records() -> None:
    source_id = "ps:assertion:source-a"
    csaf = build_bridge_csaf(
        [
            {
                "id": "claim-a",
                "concept_id": "concept-a",
                "premise_kind": "ordinary",
                "source_assertion_ids": [source_id],
            }
        ],
        [
            CanonicalJustification(
                justification_id="reported:claim-a",
                conclusion_claim_id="claim-a",
                rule_kind="reported_claim",
            )
        ],
        [],
        bundle=_make_grounded_bundle(),
    )

    projection = csaf_to_projection(
        csaf,
        [
            {
                "id": "claim-a",
                "concept_id": "concept-a",
                "premise_kind": "ordinary",
                "source_assertion_ids": [source_id],
            }
        ],
    )

    projected = projection.arguments[0]

    assert isinstance(projected.projection, ProjectionAtom)
    assert projected.projection.backend == "aspic"
    assert projected.projection.backend_atom == GroundAtom("claim-a")
    assert projected.projection.source_assertion_ids == (source_id,)
    assert projected.projection.provenance is not None
    assert projected.projection.provenance.backend == "aspic"
    assert projected.projection.provenance.source_assertion_ids == (source_id,)
    assert projected.projection.loss is None


def test_grounded_backend_projection_has_typed_loss_witness_when_source_assertion_missing() -> None:
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

    projection = csaf_to_projection(csaf, [])

    grounded_fly = next(
        argument
        for argument in projection.arguments
        if argument.projection.backend_atom == GroundAtom("fly", ("tweety",))
    )

    assert isinstance(grounded_fly.projection.loss, ProjectionLossWitness)
    assert grounded_fly.projection.loss.kind == "missing_source_assertion"
    assert grounded_fly.projection.source_assertion_ids == ()

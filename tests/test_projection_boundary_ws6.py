"""CSAF → ``StructuredProjection`` source-assertion provenance boundary (Phase 6b).

Ported from the pre-rewrite ``tests/test_projection_boundary_ws6.py``; the
grounded-bundle helper is re-expressed over the rewrite ``DefeasibleRule`` /
``grounder.ground`` surface. Pins that a claim-backed projected argument carries
a typed ``ProjectionFrameProvenanceRecord`` with its situated source-assertion
ids, while a grounded argument with no backing claim carries a typed
``ProjectionLossWitness`` instead (CLAUDE.md: provenance loss is surfaced, never
silently dropped).
"""

from __future__ import annotations

import gunray
import pytest
from argumentation.structured.aspic.aspic import GroundAtom

from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from propstore.core.active_claims import ActiveClaim
from propstore.core.justifications import CanonicalJustification
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry
from propstore.structured_projection import (
    ProjectionAtom,
    ProjectionLiftError,
    ProjectionLossWitness,
    lift_projected_argument,
)

_EMPTY_BUNDLE = GroundedRulesBundle.empty()


def _grounded_fly_bundle() -> GroundedRulesBundle:
    rule = DefeasibleRule(
        rule_id="r1",
        kind="defeasible",
        head=Atom(predicate="fly", terms=(Term(kind="var", name="X"),)),
        body=(
            BodyLiteral(
                kind="positive",
                atom=Atom(predicate="bird", terms=(Term(kind="var", name="X"),)),
            ),
        ),
    )
    return ground(
        (rule,),
        (gunray.GroundAtom(predicate="bird", arguments=("tweety",)),),
        PredicateRegistry.from_documents(()),
        return_arguments=True,
    )


def test_aspic_projection_arguments_expose_typed_source_projection_records() -> None:
    source_id = "ps:assertion:source-a"
    claim = ActiveClaim(
        claim_id="claim-a",
        concept_id="concept-a",
        source_assertion_ids=(source_id,),
    )
    csaf = build_bridge_csaf(
        [claim],
        [
            CanonicalJustification(
                justification_id="reported:claim-a",
                conclusion_claim_id="claim-a",
                rule_kind="reported_claim",
            )
        ],
        [],
        bundle=_EMPTY_BUNDLE,
    )

    projection = csaf_to_projection(csaf, [claim])
    projected = projection.arguments[0]

    assert isinstance(projected.projection, ProjectionAtom)
    assert projected.projection.backend == "aspic"
    assert projected.projection.backend_atom == GroundAtom(
        "ist",
        ("propstore:context:root", "claim-a"),
    )
    assert projected.projection.source_assertion_ids == (source_id,)
    assert projected.projection.provenance is not None
    assert projected.projection.provenance.backend == "aspic"
    assert projected.projection.provenance.source_assertion_ids == (source_id,)
    assert projected.projection.loss is None

    lifted = lift_projected_argument(projected)
    assert lifted.situated_assertion_ids == (source_id,)
    assert lifted.provenance == projected.projection.provenance


def test_grounded_projection_has_typed_loss_witness_when_source_assertion_missing() -> (
    None
):
    csaf = build_bridge_csaf([], [], [], bundle=_grounded_fly_bundle())

    projection = csaf_to_projection(csaf, [])

    grounded_fly = next(
        argument
        for argument in projection.arguments
        if argument.projection.backend_atom == GroundAtom("fly", ("tweety",))
    )

    assert isinstance(grounded_fly.projection.loss, ProjectionLossWitness)
    assert grounded_fly.projection.loss.kind == "missing_source_assertion"
    assert grounded_fly.projection.source_assertion_ids == ()

    with pytest.raises(ProjectionLiftError, match="missing_source_assertion"):
        lift_projected_argument(grounded_fly)

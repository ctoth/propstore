from __future__ import annotations

import json

from propstore.revision.projection import project_belief_base
from tests.test_revision_phase1 import _RevisionStore, _make_bound


def test_project_belief_base_exposes_support_sets_for_claim_atoms() -> None:
    store = _RevisionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = project_belief_base(bound)
    assumption_id = base.assumptions[0].assumption_id

    assert base.support_sets["claim:claim_exact"] == ((assumption_id,),)


def test_project_belief_base_exposes_essential_support_for_claim_atoms() -> None:
    store = _RevisionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = project_belief_base(bound)
    assumption_id = base.assumptions[0].assumption_id

    assert base.essential_support["claim:claim_exact"] == (assumption_id,)


def test_projected_support_metadata_is_deterministic_under_claim_order_variation() -> None:
    claims = [
        {
            "id": "claim_b",
            "concept_id": "concept_b",
            "type": "parameter",
            "value": 2.0,
            "conditions_cel": json.dumps(["x == 1"]),
        },
        {
            "id": "claim_a",
            "concept_id": "concept_a",
            "type": "parameter",
            "value": 1.0,
            "conditions_cel": json.dumps(["x == 1"]),
        },
    ]

    base_a = project_belief_base(_make_bound(_RevisionStore(claims=claims), bindings={"x": 1}))
    base_b = project_belief_base(_make_bound(_RevisionStore(claims=list(reversed(claims))), bindings={"x": 1}))

    assert base_a.support_sets == base_b.support_sets
    assert base_a.essential_support == base_b.essential_support

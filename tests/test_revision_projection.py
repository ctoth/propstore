from __future__ import annotations

import json

from propstore.revision.projection import project_belief_base
from tests.test_revision_phase1 import _RevisionStore, _make_bound


def test_project_belief_base_filters_assumptions_to_projected_claim_support() -> None:
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
    bound = _make_bound(store, bindings={"x": 1, "y": 2})

    base = project_belief_base(bound)

    assumption_cels = {assumption.cel for assumption in base.assumptions}

    assert "x == 1" in assumption_cels
    assert "y == 2" not in assumption_cels


def test_project_belief_base_is_stable_under_claim_order_variation() -> None:
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

    assert [atom.atom_id for atom in base_a.atoms] == [atom.atom_id for atom in base_b.atoms]
    assert [assumption.assumption_id for assumption in base_a.assumptions] == [
        assumption.assumption_id for assumption in base_b.assumptions
    ]


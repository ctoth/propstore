from __future__ import annotations

from propstore.support_revision.projection import project_belief_base
from tests.atms_feed import ClaimSpec, build_bound


def test_project_belief_base_exposes_support_sets_for_assertion_atoms() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("claim_exact", "concept_exact", value=1.0, conditions=("x == 1",))
        ],
        bindings={"x": 1},
    )

    base = project_belief_base(bound)
    assumption_id = base.assumptions[0].assumption_id
    atom_id = base.atoms[0].atom_id

    assert atom_id.startswith("ps:assertion:")
    assert base.support_sets[atom_id] == ((assumption_id,),)


def test_project_belief_base_exposes_essential_support_for_assertion_atoms() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("claim_exact", "concept_exact", value=1.0, conditions=("x == 1",))
        ],
        bindings={"x": 1},
    )

    base = project_belief_base(bound)
    assumption_id = base.assumptions[0].assumption_id
    atom_id = base.atoms[0].atom_id

    assert atom_id.startswith("ps:assertion:")
    assert base.essential_support[atom_id] == (assumption_id,)


def test_projected_support_metadata_is_deterministic_under_claim_order_variation() -> (
    None
):
    claims = [
        ClaimSpec("claim_b", "concept_b", value=2.0, conditions=("x == 1",)),
        ClaimSpec("claim_a", "concept_a", value=1.0, conditions=("x == 1",)),
    ]

    base_a = project_belief_base(build_bound(claims=claims, bindings={"x": 1}))
    base_b = project_belief_base(
        build_bound(claims=list(reversed(claims)), bindings={"x": 1})
    )

    assert base_a.support_sets == base_b.support_sets
    assert base_a.essential_support == base_b.essential_support

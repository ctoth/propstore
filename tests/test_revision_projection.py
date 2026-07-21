from __future__ import annotations

from propstore.support_revision.projection import project_belief_base
from tests.atms_feed import ClaimSpec, build_bound


def test_project_belief_base_includes_exact_support_claims_and_active_assumptions() -> (
    None
):
    bound = build_bound(
        claims=[
            ClaimSpec(
                "claim_exact", "concept_exact", value=1.0, conditions=("x == 1",)
            ),
            ClaimSpec(
                "claim_semantic_only",
                "concept_semantic",
                value=2.0,
                conditions=("x > 0",),
            ),
        ],
        bindings={"x": 1},
    )

    base = project_belief_base(bound)

    atom_ids = {atom.atom_id for atom in base.atoms}
    assumption_cels = {assumption.cel for assumption in base.assumptions}

    assert all(atom_id.startswith("ps:assertion:") for atom_id in atom_ids)
    assert len(atom_ids) == 1
    assert "x == 1" in assumption_cels


def test_project_belief_base_filters_assumptions_to_projected_claim_support() -> None:
    bound = build_bound(
        claims=[
            ClaimSpec("claim_exact", "concept_exact", value=1.0, conditions=("x == 1",))
        ],
        bindings={"x": 1, "y": 2},
    )

    base = project_belief_base(bound)

    assumption_cels = {assumption.cel for assumption in base.assumptions}

    assert "x == 1" in assumption_cels
    assert "y == 2" not in assumption_cels


def test_project_belief_base_is_stable_under_claim_order_variation() -> None:
    claims = [
        ClaimSpec("claim_b", "concept_b", value=2.0, conditions=("x == 1",)),
        ClaimSpec("claim_a", "concept_a", value=1.0, conditions=("x == 1",)),
    ]

    base_a = project_belief_base(build_bound(claims=claims, bindings={"x": 1}))
    base_b = project_belief_base(
        build_bound(claims=list(reversed(claims)), bindings={"x": 1})
    )

    assert [atom.atom_id for atom in base_a.atoms] == [
        atom.atom_id for atom in base_b.atoms
    ]
    assert [assumption.assumption_id for assumption in base_a.assumptions] == [
        assumption.assumption_id for assumption in base_b.assumptions
    ]

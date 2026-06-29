from __future__ import annotations

from propstore.support_revision.explain import build_revision_explanation
from propstore.support_revision.iterated import iterated_revise as iterated_revise_base
from propstore.support_revision.iterated import make_epistemic_state
from propstore.world.bound import BoundWorld
from tests.atms_feed import ClaimSpec, build_bound
from tests.support_revision.formal_realization_helpers import (
    contract_via_formal_decision,
    expand_via_formal_decision,
    revise_via_formal_decision,
)
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def _operator_bound() -> BoundWorld:
    return build_bound(
        claims=[
            ClaimSpec("legacy", "concept_legacy", value=1.0, conditions=("x == 1", "y == 2")),
            ClaimSpec("dependent", "concept_dependent", value=2.0, conditions=("y == 2",)),
            ClaimSpec("independent", "concept_independent", value=3.0, conditions=("x == 1",)),
        ],
        bindings={"x": 1, "y": 2},
    )


def _atom_id_for_claim(bound: BoundWorld, claim_id: str) -> str:
    for atom in bound.revision_base().atoms:
        if any(str(claim.claim_id) == claim_id for claim in getattr(atom, "source_claims", ())):
            return atom.atom_id
    raise AssertionError(f"missing projected claim {claim_id}")


def test_compute_entrenchment_allows_explicit_overrides_to_outrank_default_support() -> None:
    from propstore.support_revision.entrenchment import compute_entrenchment
    from propstore.support_revision.projection import project_belief_base

    bound = build_bound(
        claims=[
            ClaimSpec("claim_unconditional", "concept_base", value=1.0),
            ClaimSpec("claim_override_target", "concept_focus", value=2.0, conditions=("x == 1",)),
        ],
        bindings={"x": 1},
    )
    base = project_belief_base(bound)
    override_atom_id = next(
        atom.atom_id
        for atom in base.atoms
        if any(str(claim.claim_id) == "claim_override_target" for claim in atom.source_claims)
    )

    report = compute_entrenchment(
        bound,
        base,
        overrides={override_atom_id: {"priority": "critical"}},
    )

    assert report.ranked_atom_ids[0] == override_atom_id
    assert report.reasons[override_atom_id].override_priority == "critical"


def test_bound_world_expand_delegates_to_revision_package() -> None:
    bound = _operator_bound()
    atom = make_assertion_atom("synthetic", value=9.0)

    expected = expand_via_formal_decision(bound.revision_base(), atom)
    actual = bound.expand(atom)

    assert actual.accepted_atom_ids == expected.accepted_atom_ids
    assert actual.rejected_atom_ids == expected.rejected_atom_ids
    assert tuple(atom.atom_id for atom in actual.revised_base.atoms) == tuple(
        atom.atom_id for atom in expected.revised_base.atoms
    )


def test_bound_world_contract_delegates_to_revision_package() -> None:
    bound = _operator_bound()
    legacy_id = _atom_id_for_claim(bound, "legacy")

    expected = contract_via_formal_decision(
        bound.revision_base(),
        legacy_id,
        entrenchment=bound.revision_entrenchment(),
        max_candidates=8,
    )
    actual = bound.contract(legacy_id, max_candidates=8)

    assert actual.accepted_atom_ids == expected.accepted_atom_ids
    assert actual.rejected_atom_ids == expected.rejected_atom_ids
    assert actual.incision_set == expected.incision_set


def test_bound_world_revise_delegates_to_revision_package() -> None:
    bound = _operator_bound()
    atom = make_assertion_atom("synthetic", value=9.0)
    conflicts = {atom.atom_id: (_atom_id_for_claim(bound, "legacy"),)}

    expected = revise_via_formal_decision(
        bound.revision_base(),
        atom,
        entrenchment=bound.revision_entrenchment(),
        max_candidates=8,
        conflicts=conflicts,
    )
    actual = bound.revise(atom, conflicts=conflicts, max_candidates=8)

    assert actual.accepted_atom_ids == expected.accepted_atom_ids
    assert actual.rejected_atom_ids == expected.rejected_atom_ids
    assert actual.incision_set == expected.incision_set


def test_bound_world_revision_explain_delegates_to_explanation_builder() -> None:
    bound = _operator_bound()
    result = bound.contract(_atom_id_for_claim(bound, "legacy"), max_candidates=8)

    expected = build_revision_explanation(
        result,
        entrenchment=bound.revision_entrenchment(),
    )
    actual = bound.revision_explain(result)

    assert actual == expected


def test_bound_world_epistemic_state_delegates_to_iterated_state_builder() -> None:
    bound = _operator_bound()

    expected = make_epistemic_state(
        bound.revision_base(),
        bound.revision_entrenchment(),
    )
    actual = bound.epistemic_state()

    assert actual.accepted_atom_ids == expected.accepted_atom_ids
    assert actual.ranked_atom_ids == expected.ranked_atom_ids
    assert actual.ranking == expected.ranking


def test_bound_world_iterated_revise_delegates_to_iterated_revision_package() -> None:
    bound = _operator_bound()
    atom = make_assertion_atom("synthetic", value=9.0)
    conflicts = {atom.atom_id: (_atom_id_for_claim(bound, "legacy"),)}

    expected_result, expected_state = iterated_revise_base(
        make_epistemic_state(bound.revision_base(), bound.revision_entrenchment()),
        atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )
    actual_result, actual_state = bound.iterated_revise(
        atom,
        max_candidates=8,
        conflicts=conflicts,
        operator="restrained",
    )

    assert actual_result.accepted_atom_ids == expected_result.accepted_atom_ids
    assert actual_state.accepted_atom_ids == expected_state.accepted_atom_ids
    assert actual_state.ranked_atom_ids == expected_state.ranked_atom_ids

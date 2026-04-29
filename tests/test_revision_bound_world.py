from __future__ import annotations

import json

from propstore.support_revision.explain import build_revision_explanation
from propstore.support_revision.iterated import iterated_revise as iterated_revise_base
from propstore.support_revision.iterated import make_epistemic_state
from propstore.support_revision.operators import contract as contract_base
from propstore.support_revision.operators import expand as expand_base
from propstore.support_revision.operators import revise as revise_base
from tests.support_revision.revision_assertion_helpers import make_assertion_atom
from tests.test_revision_phase1 import _RevisionStore, _make_bound


def _operator_bound():
    store = _RevisionStore(
        claims=[
            {
                "id": "legacy",
                "concept_id": "concept_legacy",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1", "y == 2"]),
            },
            {
                "id": "dependent",
                "concept_id": "concept_dependent",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["y == 2"]),
            },
            {
                "id": "independent",
                "concept_id": "concept_independent",
                "type": "parameter",
                "value": 3.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
        ],
    )
    return _make_bound(store, bindings={"x": 1, "y": 2})


def _atom_id_for_claim(bound, claim_id: str) -> str:
    for atom in bound.revision_base().atoms:
        if any(str(claim.claim_id) == claim_id for claim in getattr(atom, "source_claims", ())):
            return atom.atom_id
    raise AssertionError(f"missing projected claim {claim_id}")


def test_bound_world_expand_delegates_to_revision_package() -> None:
    bound = _operator_bound()
    atom = make_assertion_atom("synthetic", value=9.0)

    expected = expand_base(bound.revision_base(), atom)
    actual = bound.expand(atom)

    assert actual.accepted_atom_ids == expected.accepted_atom_ids
    assert actual.rejected_atom_ids == expected.rejected_atom_ids
    assert tuple(atom.atom_id for atom in actual.revised_base.atoms) == tuple(
        atom.atom_id for atom in expected.revised_base.atoms
    )


def test_bound_world_contract_delegates_to_revision_package() -> None:
    bound = _operator_bound()
    legacy_id = _atom_id_for_claim(bound, "legacy")

    expected = contract_base(
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

    expected = revise_base(
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

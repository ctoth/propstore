from __future__ import annotations

import json

from propstore.support_revision.projection import project_belief_base
from propstore.support_revision.state import AssertionAtom
from tests.test_revision_phase1 import _RevisionStore, _make_bound


def test_project_belief_base_collapses_duplicate_rows_by_situated_assertion_identity() -> None:
    """AGM belief atoms are assertion-language sentences, not claim-row buckets."""
    store = _RevisionStore(
        claims=[
            {
                "id": "claim_first_source",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
                "source_paper": "source-a",
                "provenance_page": 1,
            },
            {
                "id": "claim_second_source",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
                "source_paper": "source-b",
                "provenance_page": 9,
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = project_belief_base(bound)

    assert len(base.atoms) == 1
    atom = base.atoms[0]
    assert isinstance(atom, AssertionAtom)
    assert atom.atom_id == str(atom.assertion.assertion_id)
    assert atom.atom_id.startswith("ps:assertion:")
    assert "claim_first_source" not in atom.atom_id
    assert "claim_second_source" not in atom.atom_id
    assert tuple(base.support_sets) == (atom.atom_id,)
    assert tuple(base.essential_support) == (atom.atom_id,)


def test_project_belief_base_keeps_rival_values_as_distinct_situated_assertions() -> None:
    """Darwiche-Pearl iterated revision needs a sentence identity finer than target concept."""
    store = _RevisionStore(
        claims=[
            {
                "id": "claim_low",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
            {
                "id": "claim_high",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 2.0,
                "conditions_cel": json.dumps(["x == 1"]),
            },
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})

    base = project_belief_base(bound)

    atom_ids = {atom.atom_id for atom in base.atoms}
    assert len(atom_ids) == 2
    assert all(atom_id.startswith("ps:assertion:") for atom_id in atom_ids)

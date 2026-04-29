from __future__ import annotations

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.operators import contract
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionScope
from tests.support_revision.revision_assertion_helpers import make_assertion_atom


def test_contract_surfaces_enumeration_exceeded_past_ceiling() -> None:
    target = make_assertion_atom("target")
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            AssumptionAtom("assumption:a0", {"assumption_id": "a0"}),
            AssumptionAtom("assumption:a1", {"assumption_id": "a1"}),
            AssumptionAtom("assumption:a2", {"assumption_id": "a2"}),
            AssumptionAtom("assumption:a3", {"assumption_id": "a3"}),
            target,
        ),
        support_sets={
            target.atom_id: (
                ("assumption:a0", "assumption:a1"),
                ("assumption:a2", "assumption:a3"),
            ),
        },
    )

    try:
        contract(
            base,
            (target.atom_id,),
            entrenchment=EntrenchmentReport(ranked_atom_ids=()),
            max_candidates=1,
        )
    except EnumerationExceeded as exc:
        assert exc.partial_count == 1
        assert exc.max_candidates == 1
        assert exc.remainder_provenance == ProvenanceStatus.VACUOUS
    else:
        raise AssertionError("contract must surface enumeration budget exhaustion")

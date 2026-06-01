from __future__ import annotations

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.state import BeliefBase, RevisionScope
from tests.support_revision.formal_realization_helpers import (
    contract_via_formal_decision,
)
from tests.support_revision.revision_assertion_helpers import (
    make_assertion_atom,
    make_assumption_atom,
)


def test_contract_surfaces_enumeration_exceeded_past_ceiling() -> None:
    target = make_assertion_atom("target")
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            make_assumption_atom("a0"),
            make_assumption_atom("a1"),
            make_assumption_atom("a2"),
            make_assumption_atom("a3"),
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
        contract_via_formal_decision(
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

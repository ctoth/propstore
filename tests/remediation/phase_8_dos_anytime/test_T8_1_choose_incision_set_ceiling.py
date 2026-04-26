from __future__ import annotations

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.support_revision.entrenchment import EntrenchmentReport
from propstore.support_revision.operators import _choose_incision_set
from propstore.support_revision.state import AssumptionAtom, BeliefBase, RevisionScope
from tests.revision_assertion_helpers import make_assertion_atom


def test_choose_incision_set_returns_enumeration_exceeded_past_ceiling() -> None:
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

    result = _choose_incision_set(
        base,
        (target.atom_id,),
        EntrenchmentReport(ranked_atom_ids=()),
        max_candidates=1,
    )

    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1
    assert result.max_candidates == 1
    assert result.remainder_provenance == ProvenanceStatus.VACUOUS

"""DoS ceilings for assignment-selection candidate enumeration."""

from __future__ import annotations

from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import ProvenanceStatus
from propstore.world.assignment_selection_merge import enumerate_candidate_assignments
from propstore.world.types import AssignmentSelectionProblem, MergeAssignment, MergeSource


def test_enumerate_candidate_assignments_returns_enumeration_exceeded_past_ceiling() -> None:
    """Zilberstein 1996 anytime framing: cap assignment Cartesian expansion."""

    problem = AssignmentSelectionProblem(
        concept_ids=("x", "y"),
        sources=tuple(
            MergeSource(
                source_id=f"s{i}",
                assignment=MergeAssignment(values={"x": f"x{i}", "y": f"y{i}"}),
            )
            for i in range(33)
        ),
    )

    result = enumerate_candidate_assignments(problem, max_candidates=1_000)

    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1_000
    assert result.remainder_provenance == ProvenanceStatus.VACUOUS

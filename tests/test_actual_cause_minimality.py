from __future__ import annotations

from propstore.world.actual_cause import actual_cause
from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import bool_scm, equation


def test_conjunctive_candidate_with_removable_conjunct_fails_ac3() -> None:
    scm = bool_scm(
        endogenous={"X", "Y", "E"},
        equations={
            "X": equation("X", ("U_X",), lambda values: values["U_X"]),
            "Y": equation("Y", ("U_Y",), lambda values: values["U_Y"]),
            "E": equation("E", ("X",), lambda values: values["X"]),
        },
        exogenous_assignment={"U_X": True, "U_Y": True},
    )

    verdict = actual_cause(
        InterventionWorld(scm, {}),
        effect=lambda values: values["E"] is True,
        candidate_cause={"X": True, "Y": True},
    )

    assert verdict.holds is False
    assert verdict.criterion == "AC3"
    assert verdict.smaller_cause == {"X": True}

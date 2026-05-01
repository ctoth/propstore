from __future__ import annotations

from propstore.world.actual_cause import actual_cause
from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import bool_scm, equation


def _disjunctive_forest_fire_world() -> InterventionWorld:
    # Halpern 2015 notes lines 101-108 and 199: with FF = max(L, MD),
    # singleton L=1 and MD=1 are parts of a joint cause under modified HP,
    # not individual causes.
    scm = bool_scm(
        endogenous={"L", "MD", "FF"},
        equations={
            "L": equation("L", ("U_L",), lambda values: values["U_L"]),
            "MD": equation("MD", ("U_MD",), lambda values: values["U_MD"]),
            "FF": equation(
                "FF",
                ("L", "MD"),
                lambda values: values["L"] or values["MD"],
            ),
        },
        exogenous_assignment={"U_L": True, "U_MD": True},
    )
    return InterventionWorld(scm, {})


def test_disjunctive_forest_fire_singletons_are_not_modified_hp_causes() -> None:
    world = _disjunctive_forest_fire_world()

    lightning = actual_cause(
        world,
        effect=lambda values: values["FF"] is True,
        candidate_cause={"L": True},
    )
    match_drop = actual_cause(
        world,
        effect=lambda values: values["FF"] is True,
        candidate_cause={"MD": True},
    )

    assert lightning.holds is False
    assert lightning.criterion == "AC2"
    assert match_drop.holds is False
    assert match_drop.criterion == "AC2"


def test_disjunctive_forest_fire_joint_cause_holds() -> None:
    verdict = actual_cause(
        _disjunctive_forest_fire_world(),
        effect=lambda values: values["FF"] is True,
        candidate_cause={"L": True, "MD": True},
    )

    assert verdict.holds is True
    assert verdict.criterion == "AC1+AC2+AC3"
    assert verdict.witness is not None
    assert verdict.witness.x_prime == {"L": False, "MD": False}

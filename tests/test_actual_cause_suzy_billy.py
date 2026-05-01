from __future__ import annotations

from propstore.world.actual_cause import actual_cause
from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import bool_scm, equation


def _suzy_billy_world() -> InterventionWorld:
    # Halpern 2015 p. 5; notes.md lines 115-129: rich rock-throwing model with
    # ST=SH=1, BT=1, BH=0, BS=1 in the actual context.
    scm = bool_scm(
        endogenous={"ST", "BT", "SH", "BH", "BS"},
        equations={
            "ST": equation("ST", ("U_S",), lambda values: values["U_S"]),
            "BT": equation("BT", ("U_B",), lambda values: values["U_B"]),
            "SH": equation("SH", ("ST",), lambda values: values["ST"]),
            "BH": equation(
                "BH",
                ("BT", "SH"),
                lambda values: values["BT"] and not values["SH"],
            ),
            "BS": equation(
                "BS",
                ("SH", "BH"),
                lambda values: values["SH"] or values["BH"],
            ),
        },
        exogenous_assignment={"U_S": True, "U_B": True},
    )
    return InterventionWorld(scm, {})


def test_suzy_throw_is_actual_cause_of_shatter() -> None:
    verdict = actual_cause(
        _suzy_billy_world(),
        effect=lambda values: values["BS"] is True,
        candidate_cause={"ST": True},
    )

    assert verdict.holds is True
    assert verdict.criterion == "AC1+AC2+AC3"
    assert verdict.witness is not None
    assert verdict.witness.x_prime == {"ST": False}


def test_billy_throw_is_not_actual_cause_of_shatter() -> None:
    verdict = actual_cause(
        _suzy_billy_world(),
        effect=lambda values: values["BS"] is True,
        candidate_cause={"BT": True},
    )

    assert verdict.holds is False
    assert verdict.criterion == "AC2"

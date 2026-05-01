from __future__ import annotations

from propstore.world.actual_cause import actual_cause
from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import bool_scm, equation


def _voting_world(yes_count: int, no_count: int) -> InterventionWorld:
    voters = {
        f"V{i}"
        for i in range(1, yes_count + no_count + 1)
    }
    equations = {
        voter: equation(
            voter,
            (f"U_{voter}",),
            lambda values, voter=voter: values[f"U_{voter}"],
        )
        for voter in voters
    }
    equations["WIN"] = equation(
        "WIN",
        tuple(sorted(voters)),
        lambda values: sum(1 for voter in voters if values[voter]) > len(voters) / 2,
    )
    exogenous_assignment = {
        f"U_V{i}": i <= yes_count
        for i in range(1, yes_count + no_count + 1)
    }
    scm = bool_scm(
        endogenous={*voters, "WIN"},
        equations=equations,
        exogenous_assignment=exogenous_assignment,
    )
    return InterventionWorld(scm, {})


def test_seven_four_majority_vote_is_not_individual_modified_hp_cause() -> None:
    # Halpern 2015 pp. 7-8; notes.md lines 174 and 187-195: modified HP blocks voting
    # anomalies produced by non-actual off-path contingencies.
    verdict = actual_cause(
        _voting_world(yes_count=7, no_count=4),
        effect=lambda values: values["WIN"] is True,
        candidate_cause={"V1": True},
    )

    assert verdict.holds is False
    assert verdict.criterion == "AC2"


def test_six_five_majority_vote_is_individual_modified_hp_cause() -> None:
    verdict = actual_cause(
        _voting_world(yes_count=6, no_count=5),
        effect=lambda values: values["WIN"] is True,
        candidate_cause={"V1": True},
    )

    assert verdict.holds is True
    assert verdict.criterion == "AC1+AC2+AC3"
    assert verdict.witness is not None
    assert verdict.witness.x_prime == {"V1": False}

from __future__ import annotations

import pytest

from propstore.world.intervention import (
    InterventionWorld,
    ObservationInconsistent,
    ObservationWorld,
)

from tests.intervention_world_helpers import simple_chain_scm


def test_observation_preserves_edges_and_is_not_intervention() -> None:
    scm = simple_chain_scm()

    observed = ObservationWorld(scm, {"Y": 1})
    intervened = InterventionWorld(scm, {"Y": 99})

    assert type(observed) is ObservationWorld
    assert type(intervened) is InterventionWorld
    assert observed.scm.equations["Y"].parents == ("X",)
    assert intervened.scm.equations["Y"].parents == ()
    assert observed.derived_value("Y").value == 1
    assert observed.trace_ids() == ("__observation_Y",)
    assert intervened.trace_ids() == ("__intervention_Y",)


def test_inconsistent_deterministic_observation_fails_closed() -> None:
    scm = simple_chain_scm()

    with pytest.raises(ObservationInconsistent) as exc_info:
        ObservationWorld(scm, {"Y": 99})

    assert exc_info.value.concept_id == "Y"
    assert exc_info.value.observed_value == 99
    assert exc_info.value.actual_value == 1

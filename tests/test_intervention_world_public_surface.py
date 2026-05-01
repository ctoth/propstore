from __future__ import annotations

import propstore
from propstore.world import (
    InterventionWorld,
    ObservationWorld,
    StructuralCausalModel,
    StructuralEquation,
    actual_cause,
)
from propstore.world.model import WorldQuery


def test_intervention_world_public_exports_are_available() -> None:
    assert propstore.InterventionWorld is InterventionWorld
    assert propstore.ObservationWorld is ObservationWorld
    assert propstore.StructuralCausalModel is StructuralCausalModel
    assert propstore.StructuralEquation is StructuralEquation
    assert propstore.actual_cause is actual_cause


def test_world_query_exposes_intervention_and_observation_methods() -> None:
    assert callable(WorldQuery.intervene)
    assert callable(WorldQuery.observe)

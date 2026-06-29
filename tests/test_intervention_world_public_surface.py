from __future__ import annotations

import propstore
from propstore.world import (
    InterventionWorld,
    ObservationWorld,
    StructuralCausalModel,
    StructuralEquation,
    actual_cause,
)

# NOTE: the WorldQuery.intervene/observe surface from the reference test depends
# on world/model.py, which lands in Phase 7a-world; this slice covers only the
# causal export surface.


def test_intervention_world_public_exports_are_available() -> None:
    assert propstore.InterventionWorld is InterventionWorld
    assert propstore.ObservationWorld is ObservationWorld
    assert propstore.StructuralCausalModel is StructuralCausalModel
    assert propstore.StructuralEquation is StructuralEquation
    assert propstore.actual_cause is actual_cause

from __future__ import annotations

import pytest

from causal_models import StructuralCausalModel
from propstore.world import InterventionWorld, InterventionWorldUnavailable


class _NoCausalModelWorld:
    def causal_model(self) -> StructuralCausalModel | None:
        return None


def test_intervention_world_construction_requires_causal_model() -> None:
    with pytest.raises(
        InterventionWorldUnavailable, match="structural causal model"
    ):
        InterventionWorld.from_world(_NoCausalModelWorld(), {"X": 1})

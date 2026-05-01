from __future__ import annotations

import pytest

from propstore.world.intervention import (
    InterventionWorld,
    InterventionWorldUnavailable,
)


class _NoCompiledGraphWorld:
    def compiled_graph(self):
        return None


def test_intervention_world_construction_requires_compiled_graph() -> None:
    with pytest.raises(InterventionWorldUnavailable, match="compiled parameterization graph"):
        InterventionWorld.from_world(_NoCompiledGraphWorld(), {"X": 1})

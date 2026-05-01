from __future__ import annotations

from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import simple_chain_scm


def test_intervention_diff_includes_post_surgery_descendants() -> None:
    world = InterventionWorld(simple_chain_scm(), {"X": 5})

    diff = world.diff()

    assert diff["X"].old_value == 0
    assert diff["X"].new_value == 5
    assert diff["Y"].old_value == 1
    assert diff["Y"].new_value == 6
    assert diff["Z"].old_value == 2
    assert diff["Z"].new_value == 7

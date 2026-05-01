from __future__ import annotations

from propstore.world.intervention import InterventionWorld

from tests.intervention_world_helpers import simple_chain_scm


def test_do_replaces_target_equation_with_constant_and_severs_incoming_edges() -> None:
    scm = simple_chain_scm()

    intervention = InterventionWorld(scm, {"Y": 99})
    post = intervention.scm

    assert post.evaluate()["Y"] == 99
    assert post.equations["Y"].parents == ()
    assert post.equations["Y"].evaluate({"X": -1000, "Y": 1}) == 99
    assert post.equations["Z"].parents == ("Y",)
    assert post.evaluate()["Z"] == 100

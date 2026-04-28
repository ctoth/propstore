from __future__ import annotations

from argumentation.preference import defeat_holds, strictly_weaker


def test_argumentation_pin_preference_empty_target_boundary_matches_defeat_path() -> None:
    assert strictly_weaker([1.0, 2.0], [], "elitist") is True
    assert strictly_weaker([1.0, 2.0], [], "democratic") is True
    assert defeat_holds("rebuts", [1.0, 2.0], [], "elitist") is False
    assert defeat_holds("rebuts", [1.0, 2.0], [], "democratic") is False

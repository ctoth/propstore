from __future__ import annotations

from argumentation.caf import (
    ClaimAugmentedAF,
    claim_level_extensions,
    claim_range,
    defeated_claims,
    inherited_extensions,
    is_i_maximal,
    is_well_formed,
)
from argumentation.dung import ArgumentationFramework


def af(args: set[str], defeats: set[tuple[str, str]]) -> ArgumentationFramework:
    return ArgumentationFramework(arguments=frozenset(args), defeats=frozenset(defeats))


def test_argumentation_pin_exposes_claim_augmented_semantics() -> None:
    caf = ClaimAugmentedAF(
        framework=af(
            {"x1", "y1", "z", "x2", "y2"},
            {
                ("y1", "x1"),
                ("y1", "z"),
                ("z", "y1"),
                ("z", "x2"),
                ("x2", "y2"),
            },
        ),
        claims={"x1": "x", "x2": "x", "y1": "y", "y2": "y", "z": "z"},
    )

    assert set(inherited_extensions(caf, semantics="preferred")) == {
        frozenset({"x", "y"}),
        frozenset({"x", "y", "z"}),
    }
    assert claim_level_extensions(caf, semantics="preferred") == (
        frozenset({"x", "y", "z"}),
    )
    assert is_i_maximal(claim_level_extensions(caf, semantics="preferred"))


def test_argumentation_pin_exposes_caf_range_and_well_formed_helpers() -> None:
    partial_attack = ClaimAugmentedAF(
        framework=af({"a1", "a2", "b"}, {("b", "a1")}),
        claims={"a1": "A", "a2": "A", "b": "B"},
    )
    well_formed = ClaimAugmentedAF(
        framework=af({"a1", "a2", "b"}, {("a1", "b"), ("a2", "b")}),
        claims={"a1": "A", "a2": "A", "b": "B"},
    )

    assert defeated_claims(partial_attack, frozenset({"b"})) == frozenset()
    assert claim_range(partial_attack, frozenset({"b"})) == frozenset({"B"})
    assert not is_well_formed(partial_attack)
    assert is_well_formed(well_formed)

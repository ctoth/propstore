from __future__ import annotations

from propstore.families.concepts.alignment import classify_relation


def test_alignment_default_keeps_distinct_conflicting_proposals_non_attacking() -> None:
    left = _proposal(
        handle="velocity",
        name="velocity",
        definition="Distance traveled per unit time.",
    )
    right = _proposal(
        handle="speed",
        name="speed",
        definition="A scalar magnitude without direction.",
    )

    assert classify_relation(left, right) == "non_attack"


def test_alignment_shared_reference_classifies_conflicting_definitions_as_attack() -> (
    None
):
    shared_uri = "tag:example.org,2026:concept/motion"
    left = _proposal(
        handle="motion_a",
        name="motion a",
        definition="A vector-valued rate of change.",
        uri=shared_uri,
    )
    right = _proposal(
        handle="motion_b",
        name="motion b",
        definition="A scalar displacement magnitude.",
        uri=shared_uri,
    )

    assert classify_relation(left, right) == "attack"

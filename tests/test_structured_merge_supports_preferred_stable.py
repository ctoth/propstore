from __future__ import annotations

from argumentation.dung import ArgumentationFramework

from propstore.merge.structured_merge import argumentation_evidence_from_projection
from propstore.structured_projection import StructuredProjection


def _two_cycle_projection() -> StructuredProjection:
    return StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset({"arg:a", "arg:b"}),
            defeats=frozenset({("arg:a", "arg:b"), ("arg:b", "arg:a")}),
            attacks=frozenset({("arg:a", "arg:b"), ("arg:b", "arg:a")}),
        ),
        claim_to_argument_ids={
            "claim_a": ("arg:a",),
            "claim_b": ("arg:b",),
        },
        argument_to_claim_id={
            "arg:a": "claim_a",
            "arg:b": "claim_b",
        },
    )


def test_structured_merge_evidence_preserves_preferred_skeptical_and_credulous_sets() -> None:
    evidence = argumentation_evidence_from_projection(
        branch="left",
        projection=_two_cycle_projection(),
        claim_assertion_ids={
            "claim_a": ("ps:assertion:a",),
            "claim_b": ("ps:assertion:b",),
        },
        semantics="preferred",
    )

    assert evidence.accepted_assertion_ids == ("ps:assertion:a", "ps:assertion:b")
    assert evidence.skeptical_assertion_ids == ()
    assert evidence.witness_assertion_ids == ("ps:assertion:a", "ps:assertion:b")


def test_structured_merge_evidence_supports_stable_semantics() -> None:
    evidence = argumentation_evidence_from_projection(
        branch="left",
        projection=_two_cycle_projection(),
        claim_assertion_ids={
            "claim_a": ("ps:assertion:a",),
            "claim_b": ("ps:assertion:b",),
        },
        semantics="stable",
    )

    assert evidence.accepted_assertion_ids == ("ps:assertion:a", "ps:assertion:b")
    assert evidence.skeptical_assertion_ids == ()

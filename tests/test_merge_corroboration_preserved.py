"""Cross-paper corroboration survives the merge math as distinct arguments.

The reference also asserted on the materialized two-parent merge commit; that storage
half lands in Phase 9. Here we assert the merge-framework math: two papers asserting
the same proposition under different source identities stay rival (distinct) arguments,
each carrying its own provenance witness.
"""

from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from tests.merge_helpers import obs_claim


def test_cross_paper_corroboration_survives_merge_framework() -> None:
    merge = build_merge_framework(
        {
            "master": [
                obs_claim("claim_a", "The same proposition", ["concept_x"], paper="left_paper")
            ],
            "paper/right": [
                obs_claim("claim_b", "The same proposition", ["concept_x"], paper="right_paper")
            ],
        },
        "master",
        "paper/right",
    )

    assert len(merge.arguments) == 2
    assert {argument.artifact_id for argument in merge.arguments} == {"claim_a", "claim_b"}
    assert len({argument.assertion_id for argument in merge.arguments}) == 2
    assert all(argument.witness_basis for argument in merge.arguments)
    papers = {argument.claim.paper for argument in merge.arguments}
    assert papers == {"left_paper", "right_paper"}

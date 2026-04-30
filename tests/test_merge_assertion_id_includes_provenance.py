from __future__ import annotations

from tests.ws_l_merge_helpers import merge_claim_from_payload, obs_claim


def test_assertion_id_distinguishes_source_paper_provenance() -> None:
    left = merge_claim_from_payload(
        obs_claim("claim_a", "The same proposition", ["concept_x"], paper="left_paper"),
        paper="left_paper",
    )
    right = merge_claim_from_payload(
        obs_claim("claim_b", "The same proposition", ["concept_x"], paper="right_paper"),
        paper="right_paper",
    )

    assert left.assertion_id != right.assertion_id

from __future__ import annotations

from tests.merge_helpers import obs_claim


def test_assertion_id_distinguishes_source_paper_provenance() -> None:
    left = obs_claim("claim_a", "The same proposition", ["concept_x"], paper="left_paper")
    right = obs_claim("claim_b", "The same proposition", ["concept_x"], paper="right_paper")

    assert left.assertion_id != right.assertion_id


def test_assertion_id_is_stable_for_same_proposition_and_provenance() -> None:
    left = obs_claim("claim_a", "The same proposition", ["concept_x"], paper="p")
    right = obs_claim("claim_b", "The same proposition", ["concept_x"], paper="p")

    assert left.assertion_id == right.assertion_id

from __future__ import annotations

from propstore.merge import merge_classifier
from tests.ws_l_merge_helpers import merge_claim_from_payload, obs_claim


def test_classify_pair_returns_unknown_when_detector_has_no_records(monkeypatch) -> None:
    monkeypatch.setattr(
        "propstore.conflict_detector.detect_conflicts",
        lambda claims, concept_registry, cel_registry: [],
    )

    left = merge_claim_from_payload(
        obs_claim("left", "Unclassified", ["concept_x"]),
    )
    same_concept = merge_claim_from_payload(
        obs_claim("right", "Different wording", ["concept_x"]),
    )
    different_concept = merge_claim_from_payload(
        obs_claim("other", "Different wording", ["concept_y"]),
    )

    assert merge_classifier._classify_pair(left, same_concept) is merge_classifier._DiffKind.UNKNOWN
    assert merge_classifier._classify_pair(left, different_concept) is merge_classifier._DiffKind.UNKNOWN

from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from tests.merge_helpers import param_claim


def test_regime_split_same_value_claims_remain_distinct_with_ignorance() -> None:
    merge = build_merge_framework(
        {
            "master": [param_claim("claim1", "concept_x", 300.0, conditions=["T < 100"])],
            "paper/regime-right": [
                param_claim("claim1", "concept_x", 300.0, conditions=["T >= 100"])
            ],
        },
        "master",
        "paper/regime-right",
    )

    assert len(merge.arguments) == 2
    assert len({argument.assertion_id for argument in merge.arguments}) == 2
    left_id, right_id = sorted(argument.assertion_id for argument in merge.arguments)
    assert (left_id, right_id) in merge.framework.ignorance
    assert (right_id, left_id) in merge.framework.ignorance
    assert not merge.framework.attacks

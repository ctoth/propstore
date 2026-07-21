from __future__ import annotations

from propstore.merge.merge_classifier import build_merge_framework
from tests.merge_helpers import obs_claim


def test_every_merge_argument_has_source_artifact_witness_basis() -> None:
    merge = build_merge_framework(
        {
            "master": [obs_claim("left", "Left", ["concept_left"], paper="left_paper")],
            "paper/right": [
                obs_claim("right", "Right", ["concept_right"], paper="right_paper")
            ],
        },
        "master",
        "paper/right",
    )

    assert merge.arguments
    for argument in merge.arguments:
        assert argument.witness_basis
        assert argument.witness_basis[0].source_artifact_id == argument.artifact_id
        assert argument.witness_basis[0].source_paper in {"left_paper", "right_paper"}

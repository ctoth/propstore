from __future__ import annotations

import pytest

from propstore.proposals import (
    UnknownProposalPath,
    commit_stance_proposals,
    plan_stance_proposal_promotion,
)
from propstore.repository import Repository


def test_plan_stance_proposal_promotion_typo_path_raises_typed_error(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    commit_stance_proposals(
        repo,
        {
            "claim_a": [
                {
                    "target": "claim_b",
                    "type": "supports",
                    "strength": "strong",
                    "note": "proposal",
                    "conditions_differ": None,
                    "resolution": {"method": "nli", "model": "test", "confidence": 0.7},
                }
            ]
        },
        "test",
    )

    with pytest.raises(UnknownProposalPath) as excinfo:
        plan_stance_proposal_promotion(repo, path="claim_typo")

    assert excinfo.value.requested_path == "claim_typo"
    assert excinfo.value.available_filenames == ("claim_a.yaml",)

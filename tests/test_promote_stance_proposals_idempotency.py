from __future__ import annotations

import pytest

from propstore.proposals import (
    ProposalAlreadyPromoted,
    commit_stance_proposals,
    plan_stance_proposal_promotion,
    promote_stance_proposals,
)
from propstore.families.registry import StanceFileRef
from propstore.repository import Repository


def _seed(repo: Repository) -> None:
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


def test_promote_stance_proposals_records_source_sha_and_rejects_repeat(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed(repo)
    plan = plan_stance_proposal_promotion(repo)
    assert plan.proposal_tip is not None

    promote_stance_proposals(repo, plan)
    promoted = repo.families.stances.require_handle(
        StanceFileRef(plan.items[0].source_claim)
    )
    assert promoted.document.promoted_from_sha == plan.proposal_tip

    with pytest.raises(ProposalAlreadyPromoted) as excinfo:
        promote_stance_proposals(repo, plan_stance_proposal_promotion(repo))

    assert excinfo.value.source_claim == "claim_a"
    assert excinfo.value.promoted_from_sha == plan.proposal_tip

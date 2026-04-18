from __future__ import annotations

from propstore.proposals import (
    STANCE_PROPOSAL_BRANCH,
    commit_stance_proposals,
    plan_stance_proposal_promotion,
    promote_stance_proposals,
)
from propstore.repository import Repository


def _seed_stance_proposal(repo: Repository) -> None:
    commit_stance_proposals(
        repo,
        {
            "claim_a": [
                {
                    "target": "claim_b",
                    "type": "supports",
                    "strength": "strong",
                    "note": "test promotion",
                    "conditions_differ": None,
                    "resolution": {
                        "method": "nli_first_pass",
                        "model": "test-model",
                        "confidence": 0.7,
                    },
                }
            ],
        },
        "test-model",
    )


def test_stance_proposal_promotion_plan_selects_committed_proposals(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_stance_proposal(repo)

    plan = plan_stance_proposal_promotion(repo)

    assert plan.branch == STANCE_PROPOSAL_BRANCH
    assert plan.proposal_tip is not None
    assert len(plan.items) == 1
    assert plan.items[0].source_claim == "claim_a"
    assert plan.items[0].source_relpath == "proposal/stances:stances/claim_a.yaml"
    assert plan.items[0].target_path == repo.root / "stances" / "claim_a.yaml"


def test_stance_proposal_promotion_commits_to_master(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_stance_proposal(repo)
    plan = plan_stance_proposal_promotion(repo)

    result = promote_stance_proposals(repo, plan)

    assert result.moved == 1
    assert "claim_a.yaml" in repo.git.list_dir("stances")


def test_stance_proposal_promotion_reports_missing_branch(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    plan = plan_stance_proposal_promotion(repo)

    assert plan.has_branch is False
    assert plan.items == ()

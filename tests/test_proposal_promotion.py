from __future__ import annotations

from types import SimpleNamespace

from click.testing import CliRunner

from propstore.app.proposals import ProposalPromotionItem, ProposalPromotionPlanReport
from propstore.cli.proposal_cmds import promote_cmd
from propstore.proposals import (
    commit_stance_proposals,
    plan_stance_proposal_promotion,
    promote_stance_proposals,
    stance_proposal_branch,
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

    assert plan.branch == stance_proposal_branch(repo)
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
    assert "claim_a.yaml" in repo.git.iter_dir("stances")


def test_stance_proposal_promotion_reports_missing_branch(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    plan = plan_stance_proposal_promotion(repo)

    assert plan.has_branch is False
    assert plan.items == ()


def test_promote_cli_reports_only_actual_promoted_items(monkeypatch) -> None:
    planned_items = (
        ProposalPromotionItem(
            source_relpath="proposal/stances:stances/claim_a.yaml",
            target_path="stances/claim_a.yaml",
            filename="claim_a.yaml",
        ),
        ProposalPromotionItem(
            source_relpath="proposal/stances:stances/claim_b.yaml",
            target_path="stances/claim_b.yaml",
            filename="claim_b.yaml",
        ),
        ProposalPromotionItem(
            source_relpath="proposal/stances:stances/claim_c.yaml",
            target_path="stances/claim_c.yaml",
            filename="claim_c.yaml",
        ),
    )
    plan = ProposalPromotionPlanReport(
        branch="proposal/stances",
        has_branch=True,
        items=planned_items,
        plan=object(),  # The mocked owner promotion does not inspect it.
    )

    monkeypatch.setattr(
        "propstore.cli.proposal_cmds.plan_proposal_promotion",
        lambda _repo, _request: plan,
    )
    monkeypatch.setattr(
        "propstore.cli.proposal_cmds.promote_proposals",
        lambda _repo, _plan: SimpleNamespace(
            moved=2,
            promoted_items=(planned_items[0], planned_items[2]),
        ),
    )

    result = CliRunner().invoke(promote_cmd, ["--yes"], obj={"repo": object()})

    assert result.exit_code == 0, result.output
    assert "Promoted: claim_a.yaml" in result.output
    assert "Promoted: claim_b.yaml" not in result.output
    assert "Promoted: claim_c.yaml" in result.output
    assert "Promoted 2 of 3 file(s)." in result.output

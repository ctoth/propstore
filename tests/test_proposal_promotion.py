from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from propstore.app.proposals import ProposalPromotionItem, ProposalPromotionPlanReport
from propstore.cli.proposal import promote
from propstore.proposals import (
    commit_stance_proposals,
    plan_stance_proposal_promotion,
    promote_stance_proposals,
    stance_proposal_branch,
)
from propstore.proposal_promotion import (
    PlannedCanonicalArtifact,
    commit_planned_canonical_artifacts,
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

    assert plan.branch == stance_proposal_branch()
    assert plan.proposal_tip is not None
    assert len(plan.items) == 1
    assert plan.items[0].artifact_id
    assert plan.items[0].source_claim == "claim_a"
    assert plan.items[0].source_relpath == f"proposal/stances:stances/{plan.items[0].filename}"
    assert plan.items[0].target_path == repo.root / "stances" / plan.items[0].filename


def test_stance_proposal_promotion_commits_to_master(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    _seed_stance_proposal(repo)
    plan = plan_stance_proposal_promotion(repo)

    result = promote_stance_proposals(repo, plan)

    assert result.moved == 1
    assert plan.items[0].filename in repo.git.iter_dir("stances")


def test_commit_planned_canonical_artifacts_saves_multiple_refs_in_one_transaction() -> None:
    class FakeWriter:
        def __init__(self) -> None:
            self.saved: list[tuple[str, str]] = []

        def save(self, ref: str, document: str) -> None:
            self.saved.append((ref, document))

    class FakeTransaction:
        def __init__(self) -> None:
            self.writer = FakeWriter()

    class FakeTransact:
        def __init__(self) -> None:
            self.messages: list[str] = []
            self.entered = 0
            self.exited = 0
            self.transaction = FakeTransaction()

        def __call__(self, *, message: str):
            self.messages.append(message)
            return self

        def __enter__(self) -> FakeTransaction:
            self.entered += 1
            return self.transaction

        def __exit__(self, exc_type, exc, tb) -> None:
            self.exited += 1

    transact = FakeTransact()

    count = commit_planned_canonical_artifacts(
        transact,
        message="Promote planned artifacts",
        family=lambda transaction: transaction.writer,
        artifacts=(
            PlannedCanonicalArtifact("ref-a", "doc-a"),
            PlannedCanonicalArtifact("ref-b", "doc-b"),
        ),
    )

    assert count == 2
    assert transact.messages == ["Promote planned artifacts"]
    assert transact.entered == 1
    assert transact.exited == 1
    assert transact.transaction.writer.saved == [("ref-a", "doc-a"), ("ref-b", "doc-b")]


def test_proposal_promotion_modules_use_shared_transaction_helper() -> None:
    proposal_sources = {
        "stances": Path("propstore/proposals.py").read_text(encoding="utf-8"),
        "predicates": Path("propstore/proposals_predicates.py").read_text(encoding="utf-8"),
        "rules": Path("propstore/proposals_rules.py").read_text(encoding="utf-8"),
    }

    for source in proposal_sources.values():
        assert "commit_planned_canonical_artifacts(" in source
    assert "transaction.stances.save(" not in proposal_sources["stances"]
    assert "transaction.predicates.save(" not in proposal_sources["predicates"]
    assert "transaction.rules.save(" not in proposal_sources["rules"]


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
        "propstore.cli.proposal.plan_proposal_promotion",
        lambda _repo, _request: plan,
    )
    monkeypatch.setattr(
        "propstore.cli.proposal.promote_proposals",
        lambda _repo, _plan: SimpleNamespace(
            moved=2,
            promoted_items=(planned_items[0], planned_items[2]),
        ),
    )

    result = CliRunner().invoke(promote, ["--yes"], obj={"repo": object()})

    assert result.exit_code == 0, result.output
    assert "Promoted: claim_a.yaml" in result.output
    assert "Promoted: claim_b.yaml" not in result.output
    assert "Promoted: claim_c.yaml" in result.output
    assert "Promoted 2 of 3 file(s)." in result.output

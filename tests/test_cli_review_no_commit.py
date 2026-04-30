from __future__ import annotations

from tests.ws_k2_cli_helpers import PAPER, init_repo, invoke, seed_rule_proposals


def test_cli_promote_rules_review_mode_prints_plan_without_commit(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_rule_proposals(repo)
    proposal_before = repo.snapshot.branch_head("proposal/rules")
    master_before = repo.snapshot.branch_head("master")

    result = invoke(repo, ["proposal", "promote-rules", "--paper", PAPER])

    assert result.exit_code == 0, result.output
    assert "rule-001" in result.output
    assert "defeasible" in result.output
    assert "low_trust" in result.output
    assert "sample_size/2" in result.output
    assert "Ioannidis 2005 p. 0697" in result.output
    assert repo.snapshot.branch_head("proposal/rules") == proposal_before
    assert repo.snapshot.branch_head("master") == master_before

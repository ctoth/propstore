from __future__ import annotations

from tests.ws_k2_cli_helpers import PAPER, init_repo, invoke, seed_rule_proposals


def test_cli_promote_rules_unknown_id_reports_typed_error_without_commit(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_rule_proposals(repo)
    before = repo.snapshot.branch_head("master")

    result = invoke(
        repo,
        [
            "proposal",
            "promote-rules",
            "--paper",
            PAPER,
            "--rule-id",
            "does-not-exist",
        ],
    )

    assert result.exit_code != 0
    assert "UnknownProposalPath" in result.output
    assert "does-not-exist" in result.output
    assert repo.snapshot.branch_head("master") == before

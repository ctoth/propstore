from __future__ import annotations

from tests.ws_k2_cli_helpers import FIXTURES, PAPER, init_repo, invoke, seed_predicates


def test_cli_propose_rules_dry_run_prints_without_commit(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_predicates(repo)
    before = repo.snapshot.branch_head("proposal/rules")

    result = invoke(
        repo,
        [
            "proposal",
            "propose-rules",
            "--paper",
            PAPER,
            "--dry-run",
            "--mock-llm-fixture",
            str(FIXTURES / "llm_rule_extraction_ioannidis.json"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "rule-001" in result.output
    assert "rule-003" in result.output
    assert repo.snapshot.branch_head("proposal/rules") == before

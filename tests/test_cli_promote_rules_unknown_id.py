from __future__ import annotations

from tests.ws_k2_cli_helpers import PAPER, init_repo, invoke, seed_rule_proposals


def test_cli_promote_rules_unknown_id_fails(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_rule_proposals(repo)

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
    assert "does-not-exist" in result.output
    # No canonical rule was written.
    assert repo.families.defeasible_rule.load("rule-001") is None

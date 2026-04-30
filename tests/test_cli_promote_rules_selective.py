from __future__ import annotations

from propstore.families.registry import RuleFileRef, RuleProposalRef
from tests.ws_k2_cli_helpers import PAPER, init_repo, invoke, seed_rule_proposals


def test_cli_promote_rules_selective_promotes_only_selected(tmp_path) -> None:
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
            "rule-001",
            "--rule-id",
            "rule-003",
        ],
    )

    assert result.exit_code == 0, result.output
    assert repo.families.rules.load(RuleFileRef(f"{PAPER}/rule-001")) is not None
    assert repo.families.rules.load(RuleFileRef(f"{PAPER}/rule-003")) is not None
    assert repo.families.rules.load(RuleFileRef(f"{PAPER}/rule-002")) is None
    assert repo.families.proposal_rules.require(RuleProposalRef(PAPER, "rule-002"))

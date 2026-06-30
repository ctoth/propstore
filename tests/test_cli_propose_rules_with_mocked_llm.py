from __future__ import annotations

from propstore.families.registry import RuleProposalRef
from tests.ws_k2_cli_helpers import FIXTURES, PAPER, init_repo, invoke, seed_predicates


def test_cli_propose_rules_records_proposals_from_fixture(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_predicates(repo)

    result = invoke(
        repo,
        [
            "proposal",
            "propose-rules",
            "--paper",
            PAPER,
            "--mock-llm-fixture",
            str(FIXTURES / "llm_rule_extraction_ioannidis.json"),
        ],
    )

    assert result.exit_code == 0, result.output
    tip = repo.git.branch_sha("proposal/rules")
    assert tip is not None
    # Nothing canonical was written by the proposal step.
    assert repo.families.defeasible_rule.load("rule-001") is None
    proposal = repo.families.proposal_rules.require(
        RuleProposalRef(PAPER, "rule-001"), commit=tip
    )
    assert proposal.predicates_referenced == ("sample_size/2", "bias/2")

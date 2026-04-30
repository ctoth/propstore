from __future__ import annotations

from propstore.families.registry import RuleProposalRef
from propstore.heuristic.rule_extraction import PROMPT_SHA
from tests.ws_k2_cli_helpers import FIXTURES, PAPER, init_repo, invoke, seed_predicates


def test_cli_propose_rules_with_mock_fixture_commits_proposals(tmp_path) -> None:
    repo = init_repo(tmp_path)
    seed_predicates(repo)

    result = invoke(
        repo,
        [
            "proposal",
            "propose-rules",
            "--paper",
            PAPER,
            "--model",
            "test-model",
            "--mock-llm-fixture",
            str(FIXTURES / "llm_rule_extraction_ioannidis.json"),
        ],
    )

    assert result.exit_code == 0, result.output
    proposal_tip = repo.snapshot.branch_head("proposal/rules")
    assert proposal_tip is not None
    proposal = repo.families.proposal_rules.require(
        RuleProposalRef(PAPER, "rule-001"),
        commit=proposal_tip,
    )
    assert proposal.extraction_provenance.prompt_sha == PROMPT_SHA
    assert set(proposal.predicates_referenced) <= {"sample_size/2", "bias/2"}

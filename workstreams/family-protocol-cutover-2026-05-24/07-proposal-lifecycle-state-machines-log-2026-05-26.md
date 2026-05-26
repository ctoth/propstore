# Proposal Lifecycle State Machines Log - 2026-05-26

Target architecture:
- Proposal promotion is lifecycle transition behavior over declared family
  metadata.
- Stance proposal behavior lives under the stance-family owner.
- Rule proposal behavior lives under the rule-family owner.
- Predicate proposal behavior lives under the predicate-family owner.
- Shared proposal diagnostics live in a proposal lifecycle support owner, not
  inside a per-kind root workflow module.

Forbidden surfaces:
- `propstore/proposals.py` as a stance root workflow module.
- `propstore/proposals_rules.py` as a rule root workflow module.
- `propstore/proposals_predicates.py` as a predicate root workflow module.
- `StanceProposalPromotionPlan`, `RuleProposalPromotionPlan`, and
  `PredicateProposalPromotionPlan`.
- `build_stance_document`.
- Dict input crossing into proposal document construction.
- Rule/predicate proposal promotion copying canonical documents by hand inside
  root workflow modules.

Search gates:
- `rg -n -F -- "StanceProposalPromotionPlan" propstore tests`
- `rg -n -F -- "RuleProposalPromotionPlan" propstore tests`
- `rg -n -F -- "PredicateProposalPromotionPlan" propstore tests`
- `rg -n -F -- "build_stance_document" propstore tests`
- `rg -n -F -- "promote_rule_proposals" propstore tests`
- `rg -n -F -- "promote_predicate_proposals" propstore tests`
- `rg -n -F -- "PredicateProposalDocument" propstore tests`
- `rg -n -F -- "RuleProposalDocument" propstore tests`

Runtime gates:
- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label proposal-lifecycle tests/test_proposals.py tests/test_rule_documents.py tests/test_predicate_documents.py`

## Iteration 1 - `stance proposal root workflow`

Slice read:
- `propstore/proposals.py`
- `propstore/app/proposals.py`
- `propstore/app/claims.py`
- `propstore/families/stances/declaration.py`
- `propstore/families/registry.py`
- `propstore/proposal_promotion.py`
- stance proposal tests

Surfaces:
- `propstore/proposals.py`
  - Disposition: delete
  - Owner after cleanup: stance-family lifecycle plus shared proposal
    lifecycle support.
  - Action: Deleted the root stance proposal workflow module.
  - Evidence: No `from propstore.proposals import` callers remain.
- `UnknownProposalPath`
  - Disposition: move
  - Owner after cleanup: shared proposal lifecycle support.
  - Action: Moved to `propstore.proposal_lifecycle`.
- `ProposalAlreadyPromoted`
  - Disposition: move
  - Owner after cleanup: shared proposal lifecycle support.
  - Action: Moved to `propstore.proposal_lifecycle`.
- Stance proposal branch/path helpers
  - Disposition: move
  - Owner after cleanup: stance-family lifecycle owner using registry
    placement metadata.
  - Action: Moved to `propstore.families.stances.lifecycle`.
- `StanceProposalPromotionPlan`
  - Disposition: delete
  - Owner after cleanup: generic proposal lifecycle plan/result plus Quire
    `FamilyRecordWrite` transition records.
  - Action: Replaced with `ProposalPromotionPlan[StanceRef]`,
    `ProposalPromotionItem[StanceRef]`, `ProposalPromotionResult[StanceRef]`,
    and a stance `promote_proposal` lifecycle transition.
- `build_stance_document`
  - Disposition: delete
  - Owner after cleanup: typed stance proposal input converted by the
    stance-family lifecycle owner.
  - Action: Replaced with `StanceProposalInput` and
    `build_stance_proposal_document`.

Gate results:
- Pass: `rg -n -F -- "StanceProposalPromotionPlan" propstore tests`
- Pass: `rg -n -F -- "build_stance_document" propstore tests`
- Pass: `rg -n -F -- "from propstore.proposals import" propstore tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label stance-proposal-lifecycle tests/test_proposal_promotion.py tests/test_promote_stance_proposals_idempotency.py tests/test_plan_stance_proposal_promotion_typo_path.py tests/test_commit_stance_proposals_empty_input.py tests/test_commit_stance_proposals_commit_sha_inside_with.py tests/test_proposal_paths_no_placeholder_owner.py tests/test_relate_opinions.py::TestStanceYamlRoundTrip tests/test_relate_opinions.py::TestStanceProposalsUseBranchState`
  - Evidence: `logs/test-runs/stance-proposal-lifecycle-20260526-004255.log`,
    14 passed.

Commit:
- `285b84f9 Move stance proposals to lifecycle records`

Next slice:
- Rule proposal root workflow.

## Iteration 2 - `rule proposal root workflow`

Slice read:
- `propstore/proposals_rules.py`
- `propstore/families/rules/declaration.py`
- `propstore/families/rules/lifecycle.py`
- `propstore/cli/proposal.py`
- rule proposal tests

Surfaces:
- `propstore/proposals_rules.py`
  - Disposition: delete
  - Owner after cleanup: `propstore.families.rules.lifecycle`
  - Action: Deleted the rule root proposal workflow module.
  - Evidence: No `propstore.proposals_rules` imports remain.
- `RuleProposalPromotionPlan`
  - Disposition: delete
  - Owner after cleanup: generic `ProposalPromotionPlan[RuleProposalRef]`.
  - Action: Replaced with shared proposal lifecycle plan/item/result types.
- `promote_rule_proposals`
  - Disposition: delete
  - Owner after cleanup: `apply_rule_proposal_promotion` in the rule-family
    lifecycle owner.
  - Action: Rule promotion now runs the `promote_proposal` lifecycle
    transition on `AUTHORED_RULE_PROPOSAL_CHARTER` and applies emitted
    `FamilyRecordWrite` records.
- Rule canonical document copying
  - Disposition: move
  - Owner after cleanup: rule-family lifecycle materializer.
  - Action: Moved proposal-to-canonical rule document construction into
    `_materialize_rule_proposal`.

Gate results:
- Pass: `rg -n -F -- "RuleProposalPromotionPlan" propstore tests`
- Pass: `rg -n -F -- "promote_rule_proposals" propstore tests`
- Pass: `rg -n -F -- "propstore.proposals_rules" propstore tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label rule-proposal-lifecycle tests/test_promote_rules_proposals.py tests/test_cli_promote_rules_selective.py tests/test_cli_promote_rules_unknown_id.py tests/test_cli_review_no_commit.py tests/test_proposal_promotion.py::test_proposal_promotion_modules_use_shared_transaction_helper`
  - Evidence: `logs/test-runs/rule-proposal-lifecycle-20260526-004934.log`,
    7 passed.

Commit:
- `398bb3e5 Move rule proposals to lifecycle records`

Next slice:
- Predicate proposal root workflow.

## Iteration 3 - `predicate proposal root workflow`

Slice read:
- `propstore/proposals_predicates.py`
- `propstore/families/predicates/declaration.py`
- `propstore/families/predicates/lifecycle.py`
- `propstore/cli/proposal.py`
- predicate proposal tests

Surfaces:
- `propstore/proposals_predicates.py`
  - Disposition: delete
  - Owner after cleanup: `propstore.families.predicates.lifecycle`
  - Action: Deleted the predicate root proposal workflow module.
  - Evidence: No `propstore.proposals_predicates` imports remain.
- `PredicateProposalPromotionPlan`
  - Disposition: delete
  - Owner after cleanup: generic
    `ProposalPromotionPlan[PredicateProposalRef]`.
  - Action: Replaced with shared proposal lifecycle plan/item/result types.
- `promote_predicate_proposals`
  - Disposition: delete
  - Owner after cleanup: `apply_predicate_proposal_promotion` in the
    predicate-family lifecycle owner.
  - Action: Predicate promotion now runs the `promote_proposal` lifecycle
    transition on `PREDICATE_PROPOSAL_CHARTER` and applies emitted
    `FamilyRecordWrite` records.
- Predicate canonical document copying
  - Disposition: move
  - Owner after cleanup: predicate-family lifecycle materializer.
  - Action: Moved proposal-to-canonical predicate document construction into
    `_materialize_predicate_proposal`.

Gate results:
- Pass: `rg -n -F -- "PredicateProposalPromotionPlan" propstore tests`
- Pass: `rg -n -F -- "promote_predicate_proposals" propstore tests`
- Pass: `rg -n -F -- "propstore.proposals_predicates" propstore tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label predicate-proposal-lifecycle tests/test_promote_predicates_proposals.py tests/test_proposal_promotion.py::test_proposal_promotion_modules_use_shared_transaction_helper`
  - Evidence: `logs/test-runs/predicate-proposal-lifecycle-20260526-005646.log`,
    4 passed.

Commit:
- Pending.

Next slice:
- Remove remaining handwritten proposal document shapes once state-conditional
  generated documents can own them.

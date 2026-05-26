# 07 Proposal Lifecycle State Machines

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`
- `06-source-lifecycle-state-machines.md`

## Target

Proposal branches are lifecycle states over family fields and placements. They
are not per-kind root workflow modules that copy document fields by hand.

## Deletion Targets

- `propstore/proposals.py` proposal-specific plan/result dataclasses
- `propstore/proposals_rules.py` rule proposal promotion plan/result copying
- `propstore/proposals_predicates.py` predicate proposal promotion plan/result
  copying
- `StanceProposalPromotionPlan`
- `RuleProposalPromotionPlan`
- `PredicateProposalPromotionPlan`
- branch and target-ref hardcoding that duplicates family placement metadata
- dict input accepted by proposal document builders
- `PredicateProposalDocument` and `RuleProposalDocument` as separate persisted
  handwritten document shapes after state-conditional generated documents
  exist

## Kept Behavior

- Proposal branch selection.
- Already-promoted detection.
- Conflict checks.
- Promotion provenance.
- Atomic commit behavior.
- Stance, rule, and predicate promotion semantics.

## Execution

1. Delete one proposal root workflow first.
2. Use failures to add generic lifecycle transition declarations to the
   owning family/proposal state.
3. Represent proposal-vs-canonical field differences with
   `CharterField.states`, not separate document classes.
4. Replace copied document construction with generated family document/model
   transition.
5. Repeat for the other proposal kinds.

## Search Gates

```powershell
rg -n -F -- "StanceProposalPromotionPlan" propstore tests
rg -n -F -- "RuleProposalPromotionPlan" propstore tests
rg -n -F -- "PredicateProposalPromotionPlan" propstore tests
rg -n -F -- "build_stance_document" propstore tests
rg -n -F -- "promote_rule_proposals" propstore tests
rg -n -F -- "promote_predicate_proposals" propstore tests
rg -n -F -- "PredicateProposalDocument" propstore tests
rg -n -F -- "RuleProposalDocument" propstore tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label proposal-lifecycle tests/test_proposal_promotion.py tests/test_rule_documents.py tests/test_predicate_documents.py
```

## Completion

- Proposal promotion is generic lifecycle transition behavior over declared
  proposal/canonical family metadata.

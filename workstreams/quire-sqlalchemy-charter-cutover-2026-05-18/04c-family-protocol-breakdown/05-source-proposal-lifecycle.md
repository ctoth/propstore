# 05 Source And Proposal Lifecycle

## Final State

Source-local authoring, finalize, promote, alignment, and proposal promotion
are lifecycle transitions over typed family records. Source-local and canonical
states are field metadata and family lifecycle state, not root helper modules
that rewrite dictionaries or rebuild document classes.

## Delete First

Delete the root helper surfaces as lifecycle capabilities become available:

- `propstore/source/claim_concepts.py` hardcoded claim concept field rewriting.
- `propstore/source/common.py` one-loader-per-source-family fanout.
- `propstore/source/claims.py` dict payload reconstruction and source claim
  identity rewriting.
- `propstore/source/relations.py` dict payload normalization for justifications
  and stances.
- `propstore/source/registry.py` source concept projection records and dict
  previews.
- `propstore/source/finalize.py` handwritten finalize report/document shape.
- `propstore/source/promote.py` concrete document-class promotion plan shape.
- `propstore/source/alignment.py` root alignment workflow shape.
- `propstore/proposals.py`, `propstore/proposals_rules.py`, and
  `propstore/proposals_predicates.py` proposal-specific plan/result classes and
  field-copy promotion.

## Repair Owners

- Source family lifecycle owner: source branch setup, source metadata, notes,
  source status, finalize, promote.
- Claim/concept/relation/justification/stance family owners: transition
  callbacks and validation.
- Quire lifecycle metadata: state transitions and source-local/canonical field
  placement.
- Proposal state machine: generic proposal-to-canonical lifecycle transition
  over family metadata.

## Search Gates

```powershell
rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests
rg -n -F -- "convert_document_value(" propstore/source propstore/families tests
rg -n -F -- "SourceClaimDocument" propstore/source propstore tests
rg -n -F -- "SourceConceptEntryDocument" propstore/source propstore tests
rg -n -F -- "SourceJustificationDocument" propstore/source propstore tests
rg -n -F -- "SourceStanceEntryDocument" propstore/source propstore tests
rg -n -F -- "from propstore.families.documents" propstore/source
rg -n -F -- "StanceProposalPromotionPlan" propstore tests
rg -n -F -- "RuleProposalPromotionPlan" propstore tests
rg -n -F -- "PredicateProposalPromotionPlan" propstore tests
rg -n -F -- "build_stance_document" propstore tests
rg -n -F -- "promote_rule_proposals" propstore tests
rg -n -F -- "promote_predicate_proposals" propstore tests
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-proposal-lifecycle tests/test_source_claims.py tests/test_source_relations.py tests/test_source_promotion_alignment.py tests/test_source_promote_dangling_refs.py tests/test_finalize_micropub_required.py tests/test_proposals.py
```

## Completion

- [ ] Source-local and canonical transitions are lifecycle transitions.
- [ ] Root source helper surfaces no longer own document shape or relationship
      field rewrites.
- [ ] Proposal promotion is generic lifecycle behavior.
- [ ] Search, type, and test gates pass.

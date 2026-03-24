# Phase 3: Deduplicate embed.py

## Goal
Deduplicate claim/concept parallel code in `propstore/embed.py` via generic functions.

## Done
- Read full embed.py (776 lines original)
- Identified 4 pairs of duplicated functions
- Created `_EmbedConfig` dataclass + `_embed_entities()` generic function
- Created `_FindConfig` dataclass + `_find_similar_entities()` generic function
- Created `_find_similar_agree_generic()` and `_find_similar_disagree_generic()`
- Converted all 8 public functions to thin wrappers
- Moved `_resolve_concept_id` before its first reference to fix definition ordering
- Module imports successfully

## Baseline
- 1 pre-existing test failure: `test_missing_claims_key_errors` (unrelated to embed.py)
- 505 tests pass

## Next
- Run full test suite to verify nothing broke
- Count lines to measure reduction
- Commit if tests pass
- Write report to `./reports/phase3-report.md`

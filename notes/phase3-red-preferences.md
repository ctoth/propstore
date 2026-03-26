# Phase 3 Red: Fixed-Length Preference Vectors

## Date: 2026-03-25

## GOAL
Write 8 failing tests for fixed-length (3-element) preference vectors in `claim_strength()`.

## Observations
- Read prompt at `prompts/phase3-red-preferences.md`
- Read paper notes: Modgil 2018 (Def 19 elitist/democratic), Prakken 2010 (preference orderings)
- Read `propstore/preference.py`: `claim_strength()` lines 60-92 returns variable-length vectors
  - Only includes dimensions for metadata fields that are present
  - Empty claims get `[1.0]` (single element)
  - This makes cross-claim comparison meaningless when metadata profiles differ
- Read `tests/test_preference.py`: 386 lines, has concrete + Hypothesis tests
  - Uses strategies: `_strengths`, `_strength_sets`, `_comparisons`, etc.
  - Existing tests assert variable-length behavior (e.g., `len(result) == 1` for single-field claims)

## Tests to Write (8 total)
### Example-based (5):
1. `test_claim_strength_fixed_length_all_fields` - all 3 fields → len == 3
2. `test_claim_strength_fixed_length_no_fields` - no fields → len == 3, result == [0.0, 1.0, 0.5]
3. `test_claim_strength_fixed_length_partial` - only sample_size → len == 3, defaults for missing
4. `test_claim_strength_fixed_length_different_partials` - different partials → both len == 3
5. `test_strictly_weaker_same_length_vectors` - different metadata subsets → same-length vectors

### Hypothesis (3):
6. `test_claim_strength_always_three_elements` - arbitrary claim dicts → len == 3
7. `test_strictly_weaker_irreflexive` - length-3 vectors → not weaker than self
8. `test_defeat_holds_undercuts_always_true` - undercuts always True regardless of strengths

## Why Tests Will Fail
- Tests 1-6: Current code returns variable-length vectors (1-3 elements), not fixed 3
- Test 2: Current code returns `[1.0]` for empty claims, not `[0.0, 1.0, 0.5]`
- Tests 7-8: Should pass with current code (irreflexivity and undercut properties hold already) — WAIT, need to check prompt again

## NEXT
Write the tests, run them, verify failure, commit.

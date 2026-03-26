# Iter1 Red Phase B — MC Probability Tests Session

**Date:** 2026-03-25
**Goal:** Write failing tests for 3 bugs: mc_confidence ignored, float equality on MC probs, float inequality in hypothetical conflicts.

## Observations

### Bug 1: mc_confidence ignored (praf.py:395)
- Line 395: `ci = 1.96 * math.sqrt(p_hat * (1.0 - p_hat) / n)` — hardcoded z=1.96
- Line 375: stopping criterion also implicitly assumes z=1.96
- `mc_confidence` parameter is accepted but never used to compute z
- Test written in `tests/test_praf.py` — calls MC twice with 0.95 and 0.99, asserts 0.99 CI is wider

### Bug 2: Float equality on MC probabilities (resolution.py:248)
- Line 248: `best_claims = [cid for cid, p in target_probs.items() if p == best_prob]`
- Uses `==` to compare MC-sampled floats — ties may be missed due to FP noise
- Need to write test in `tests/test_world_model.py`
- Plan: mock `_resolve_praf` internals or directly test the comparison logic

### Bug 3: Float inequality in hypothetical conflicts (hypothetical.py:142)
- Line 142: `if val_a != val_b:` — direct float comparison
- Two values differing by FP noise (e.g., 9.8 vs 9.8+1e-15) flagged as conflicting
- Test goes in `tests/test_world_model.py`
- Plan: create HypotheticalWorld with two synthetic claims whose values differ by 1e-15, call recompute_conflicts

## State
- Test 1 DONE — added to tests/test_praf.py as test_mc_confidence_affects_ci_width
- Test 2 TODO — need to add to tests/test_world_model.py
- Test 3 TODO — need to add to tests/test_world_model.py
- Haven't run any tests yet

## Files
- `tests/test_praf.py` — edited (test 1 added)
- `tests/test_world_model.py` — to be edited (tests 2 and 3)
- `reports/iter1-red-b.md` — to be written after tests run

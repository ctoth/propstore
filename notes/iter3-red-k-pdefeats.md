# Iter3 Red K: PrAF p_defeats key mismatch

**Date:** 2026-03-25
**Task:** Write failing tests for Finding 13 from audit-praf-probabilistic.md

## Observations

1. **The bug is real.** `_sample_subgraph` (praf.py:276) does `praf.p_defeats[(f, t)]` with no fallback. If a defeat is in `framework.defeats` but not in `p_defeats`, it crashes with KeyError.

2. **Component decomposition creates the inconsistency.** Lines 342-345 build `comp_p_defeats` with `if d in praf.p_defeats` filter, dropping defeats missing from p_defeats. But `comp_defeats` (lines 325-328) includes ALL defeats. Result: `comp_praf.framework.defeats` has entries not in `comp_praf.p_defeats`.

3. **First test attempt passed because of deterministic shortcut.** When ALL p_defeats in a component are missing, `comp_p_defeats` is empty, `all()` on empty is True, so `comp_all_det = True` and the component takes the deterministic path (lines 354-362), never reaching `_sample_subgraph`. The bug only triggers when a component has BOTH probabilistic defeats (sub-unity) AND missing p_defeats entries.

4. **Fix for test 14:** Put the missing-p_defeats defeat in the SAME component as probabilistic defeats. Used a 3-node single-component AF: a<->b (probabilistic) + a->c (no p_defeats entry). This forces MC sampling for the component AND hits the missing key.

5. **Test 14 fails correctly** with `KeyError: ('a', 'c')` at praf.py:276.

6. **Test 15 redesigned** from `pytest.raises(KeyError)` (which passed = green, wrong for red phase) to asserting correct behavior (should not crash, should treat missing defeat as deterministic). Now should also fail with KeyError.

## Current state

- Test 14: FAILS (KeyError) -- correct for red phase
- Test 15: Just edited, needs verification run
- Next: run tests, commit, write report

## Files

- `C:/Users/Q/code/propstore/tests/test_praf.py` -- two new tests added at end (tests 14, 15)
- `C:/Users/Q/code/propstore/propstore/praf.py` -- source with bug (lines 276, 342-345)

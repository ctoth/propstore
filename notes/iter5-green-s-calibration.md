# Iter 5 Green S: Calibration Evidence Fix

**Date:** 2026-03-25

## GOAL
Fix CorpusCalibrator.to_opinion() to use effective local sample size instead of raw corpus size, plus add SQLite CHECK constraint for opinion validity.

## Observations

### Current bug (calibrate.py:143)
`to_opinion()` passes `self._n` (corpus size) directly to `from_probability(p, n)`.
- 10k corpus -> u = 2/(10002) = 0.0002 (near-dogmatic, WRONG)
- 1 element -> u = 2/3 = 0.667 (not vacuous enough)

### Required fix (from prompt)
Implement effective sample size based on local CDF density:
1. Count reference distances within a local window around query distance
2. Cap at min(local_count, 50)
3. Single element -> u > 0.9
4. Large corpus -> u > 0.01

Formula (Sensoy 2018 p.3-4): r = p * n_eff, s = (1-p) * n_eff
Then b = r/(r+s+2), d = s/(r+s+2), u = 2/(r+s+2)

### SQLite CHECK constraint needed
- conftest.py:27-47 - test schema for `claim_stance` lacks CHECK
- build_sidecar.py:832-855 - production schema lacks CHECK
- Both need: `CHECK (abs(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) < 0.01)`

### Tests (test_calibrate.py)
3 failing:
1. test_large_corpus_does_not_produce_near_dogmatic_opinion - asserts u > 0.01
2. test_single_element_corpus_produces_near_vacuous_opinion - asserts u > 0.9
3. test_sqlite_rejects_invalid_opinion_sum - expects IntegrityError

2 passing (should stay green):
4. test_opinion_bdu_sum_invariant
5. test_monotonic_evidence_uncertainty_relationship

### Existing passing tests that must not break
- test_corpus_calibrator_uncertainty_scales_with_n (line 117) - larger corpus -> less u (monotonic)
- test_corpus_calibrator_percentile_bounds
- test_corpus_calibrator_monotonicity

## PLAN
1. Implement `_effective_sample_size(self, distance)` in CorpusCalibrator
2. Use local density window (e.g., bandwidth = 1/sqrt(n) or similar)
3. Count points within window, cap at 50
4. Update `to_opinion()` to use n_eff
5. Add CHECK constraint to conftest.py and build_sidecar.py
6. Run tests, verify all pass

## NEXT
Implement the fix.

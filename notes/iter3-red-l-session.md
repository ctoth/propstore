# Iter3 Red L — Property Tests Session

**Date:** 2026-03-25
**Goal:** Write 3 Hypothesis property tests for F27, F28, F29.

## Status: IN PROGRESS

## What I Know

### Test 1 (F27) — Dung AF with attacks != defeats
- File: `tests/test_dung.py`
- Existing `argumentation_frameworks` strategy generates AFs with `attacks=None` (line 54)
- Need a NEW strategy that generates AFs where attacks is superset of defeats
- Property: grounded extension subset of every preferred extension
- The existing `test_subset_of_every_preferred` test (line 291) already tests this for pure AFs
- Need to test it when attacks != defeats (the post-hoc pruning path in `dung.py` lines 126-150)

### Test 2 (F28) — MC with P_A < 1.0
- File: `tests/test_praf.py`
- All existing MC tests use `Opinion.dogmatic_true()` for p_args
- Need to create PrAF with P_A < 1.0, run MC, verify acceptance_probability <= P_A
- Need to read praf.py source to understand sampling logic

### Test 3 (F29) — Opinion fusion commutativity + vacuous identity
- File: `tests/test_opinion.py`
- Existing tests have concrete commutativity tests (class TestConsensusCommutative) but NOT Hypothesis-based
- Need Hypothesis property tests for:
  - `consensus_pair(a, b) == consensus_pair(b, a)` with random opinions
  - `consensus_pair(a, vacuous) ≈ a` (identity element)

## Source Code Observations

### dung.py
- `ArgumentationFramework(arguments, defeats, attacks=None)` — attacks is optional
- `grounded_extension` computes least fixed point of F over defeats, then post-hoc prunes for attack-CF (lines 126-150)
- `preferred_extensions` delegates to Z3 by default, brute-force filters complete extensions
- `admissible(s, all_args, defeats, attacks=None)` checks CF against attacks, defense against defeats
- `conflict_free(s, relation)` checks pairwise

### praf.py
- `ProbabilisticAF(framework, p_args, p_defeats)` — p_args maps arg->Opinion, p_defeats maps defeat->Opinion
- `_sample_subgraph` samples args with `rng.random() < p_a` (line 269), then samples defeats
- `PrAFResult.acceptance_probs` is dict[str, float]
- `compute_praf_acceptance(praf, strategy="mc", mc_epsilon=..., rng_seed=...)` is the entry point

### opinion.py
- `consensus_pair(a_op, b_op)` — Josang Theorem 7 formula
- `Opinion.vacuous(a=0.5)` — (0, 0, 1, a)
- Raises ValueError for two dogmatic opinions

## Results

All 7 tests PASS (as expected — these fill coverage gaps, not prove bugs):

- F27: `test_grounded_subset_of_every_preferred` PASSED, `test_grounded_conflict_free_wrt_attacks` PASSED
- F28: `test_mc_pa_lt_one_acceptance_bounded` PASSED, `test_mc_pa_lt_one_with_defeats` PASSED
- F29: `test_commutativity` PASSED, `test_vacuous_identity` PASSED, `test_vacuous_identity_different_base_rate` PASSED

## Status: DONE — committing and writing report

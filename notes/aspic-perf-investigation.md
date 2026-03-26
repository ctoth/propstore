# ASPIC+ Performance Investigation

**Date:** 2026-03-25
**GOAL:** Find why ASPIC+ tests went from 40s to 40min.

## Key Finding: TWO BOTTLENECKS

### Bottleneck 1: Z3 constraint construction in dung_z3.py (per-call cost)

For large AFs (100+ arguments), `z3_complete_extensions()` spends >90% of time
in the Z3 Python wrapper constructing Or() clauses. This is O(|args|^2 * |defeats|)
in Z3 FFI calls.

**Profiling evidence** (122 args, 5813 defeats):
- 23.4s total, 21.4s (91%) in `z3.py:Or()`
- 81M function calls, 439K Z3 Bool refs processed
- Root cause: defense+fixpoint loops generate ~9000 Or() clauses averaging 48 terms each
- Secondary: `attackers_of()` does O(|defeats|) linear scan per call, called 244 times

### Bottleneck 2: Cumulative Hypothesis volume (200 examples * many tests)

**Actual test timing observed:**
- Rationality Postulate tests (9 tests, 200 examples each using well_formed_csaf): **35s**
- Defeat tests (10 tests, running): expected ~40s based on similar workload
- Attack tests (8 tests, 200 examples each with build_arguments+compute_attacks): ~20s
- Argument construction tests (12 tests, 200 examples each with build_arguments): ~15s
- Language/rule/transposition tests (17 tests): ~5s

**Estimated total: ~115-130s with small examples.** The 40-minute figure likely occurs when
Hypothesis discovers or replays examples that produce larger argument sets (>50 args).

### The multiplier: Hypothesis database saves pathological examples

The `.hypothesis/examples/` directory has 17 saved example files. If any of these
produce frameworks with 50-100+ arguments, the Z3 bottleneck kicks in hard:
- 50 args: ~1-2s per complete_extensions call
- 100 args: ~10-20s per complete_extensions call
- Each well_formed_csaf test calls complete_extensions in the strategy itself
- 9 Rationality tests * 200 examples = 1800 complete_extensions calls

If even 5% of examples hit 50+ args: 90 calls * 2s = 180s = 3 min
If Hypothesis replays a 100-arg example across all tests: 9 * 20s = 180s per example

## Test class breakdown

| Class | Tests | Strategy | Heavy calls per example |
|-------|-------|----------|-------------------------|
| TestLanguageProperties | 6 | logical_language() | none |
| TestRuleProperties | 5 | logical_language+rules | none |
| TestTranspositionClosure | 4 | logical_language+rules | transposition_closure |
| TestArgumentConstructionProperties | 12 | full pipeline minus attacks | build_arguments |
| TestAttackProperties | 8 | full pipeline minus defeats | build_arguments + compute_attacks |
| TestDefeatProperties | 8 | full pipeline | all + compute_defeats |
| TestRationalityPostulates | 8 | well_formed_csaf | all + complete_extensions |
| Concrete tests | 7 | hand-built | varies |

Total property tests: 51, each with max_examples=200 = 10,200 Hypothesis examples.

## Confirmed observations

1. aspic.py `build_arguments` is fast (0.003s for 122 args) -- NOT the bottleneck
2. aspic.py `compute_attacks` is moderate (0.28s for 122 args, 6399 attacks)
3. aspic.py `compute_defeats` is fast (0.048s)
4. dung_z3.py `z3_complete_extensions` is the dominant cost (7-23s for 122 args)
5. With typical Hypothesis examples (4-9 args), each test is fast (~0.01s)
6. One test (test_rebutting_symmetry_for_contradictories) FAILS currently

## aspic.py secondary issues (not primary bottleneck but will matter at scale)

- `sub()`, `prem()`, `def_rules()`, `prem_p()`, `last_def_rules()`: all recursive, none memoized
- `is_firm()` and `is_strict()` called in compute_attacks inner loop: each recurses full tree
- `_all_concs()` called per combo in build_arguments product loop: no caching
- `attackers_of()` in dung.py: linear scan of defeats frozenset per call

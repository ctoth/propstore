# ASPIC+ Performance Fix: Memoize Property Functions

## 2026-03-26

### Goal
Add `functools.cache` to recursive property functions in `propstore/aspic.py` to eliminate redundant tree traversals in `compute_attacks()` and `compute_defeats()`.

### Observations
- **Before fix (with `-x`):** 36 passed, 1 failed in 25.34s
- **After fix (with `-x`):** 36 passed, 1 failed in 23.18s
- **After fix (full suite, skipping pre-existing failure):** 57 passed in 239.50s (4 min)
- Pre-existing failure: `test_rebutting_symmetry_for_contradictories` — NOT caused by this change

### What was done
Added `@functools.cache` to 7 functions in `propstore/aspic.py`:
- `conc()`, `prem()`, `sub()`, `top_rule()`, `def_rules()`, `last_def_rules()`, `prem_p()`
- `is_firm()` and `is_strict()` delegate to cached `prem_p()`/`def_rules()`, so no decorator needed

### Files
- `/c/Users/Q/code/propstore/propstore/aspic.py` — the fix

### Status
- Waiting for full test suite run to confirm all green
- Then: commit and write report

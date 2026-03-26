# Phase 5: value_si in Sidecar — Session Notes

## GOAL
Add `value_si`, `lower_bound_si`, `upper_bound_si` columns to the sidecar claim table, populated at build time via `normalize_to_si()`.

## RED PHASE — DONE
4 tests written in TestClaimValueSI class at end of test_build_sidecar.py. All 4 fail with:
`sqlite3.OperationalError: no such column: value_si` (and `lower_bound_si`)

## GREEN PHASE — IN PROGRESS
Edits done so far in `propstore/build_sidecar.py`:
1. Added `normalize_to_si, FormDefinition` to imports (line 26)
2. Added 3 columns to CREATE TABLE claim: `value_si REAL, lower_bound_si REAL, upper_bound_si REAL`
3. In `build_sidecar()`: resolve forms_dir and load `_form_registry`, pass to `_populate_claims`
4. `_populate_claims` signature updated with `form_registry` kwarg, passes to `_prepare_claim_insert_row`
5. `_prepare_claim_insert_row` signature updated with `form_registry` kwarg

## REMAINING
- Add SI normalization logic inside `_prepare_claim_insert_row` (compute value_si, lower_bound_si, upper_bound_si)
- Add the 3 new keys to the returned dict (after "unit" key)
- Run tests, verify green
- Run full suite
- Commit

## FILES
- `propstore/build_sidecar.py` — main target
- `propstore/form_utils.py` — normalize_to_si (read-only)
- `tests/test_build_sidecar.py` — 4 new tests

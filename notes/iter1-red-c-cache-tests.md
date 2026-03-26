# Iter1 Red C — Cache Clearing Tests — 2026-03-25

## GOAL
Write failing tests that expose missing cache-clearing functions in form_utils.py and unit_dimensions.py.

## OBSERVATIONS
- `form_utils.py:56`: `_form_cache` is a module-level dict, never cleared. `load_form()` populates it. No `clear_form_cache()` exists.
- `unit_dimensions.py:33`: `_symbol_table` is a module-level dict, lazy-loaded, never reset. `register_form_units()` mutates it. No `clear_symbol_table()` exists.
- Existing `tests/test_form_utils.py` imports `_form_cache` directly and manually pops entries. Uses `forms_dir` fixture pointing to real forms, and `tmp_path` for synthetic forms.
- Existing `tests/test_form_dimensions.py` tests dimension schema validation, form loading, CLI. Uses `_write_form_yaml` helper, `_MockRepo`, hypothesis strategies.

## PLAN
1. Add test to `tests/test_form_utils.py`: import `clear_form_cache`, call it, verify cache is empty. Should fail with ImportError.
2. Add test to `tests/test_form_dimensions.py`: import `clear_symbol_table`, call it, verify table is empty. Should fail with ImportError.

## STATUS
- Reading done, writing tests next.

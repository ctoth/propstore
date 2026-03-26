# Fix 4B: Future Bindings Session Notes

## GOAL
Fix `_future_engine` in atms.py to include queryable bindings in the future environment's `bindings` dict.

## DONE
1. Read prompt and 4A report
2. Traced the bug: `_future_engine` (atms.py:1108-1144) creates future environment via `replace()` updating `assumptions` and `effective_assumptions` but NOT `bindings`
3. Confirmed `Environment.bindings` is a `Mapping[str, Any]` used by BoundWorld to build `_bindings` and `_binding_conds`
4. Wrote failing test `test_future_engine_includes_queryable_bindings_in_environment` in test_atms_engine.py -- confirmed RED
5. Added `cel_to_binding()` function in labelled.py to reverse `binding_condition_to_cel()`
6. Added import of `cel_to_binding` in atms.py

## FILES
- `propstore/world/atms.py` -- _future_engine method needs bindings update (line ~1133)
- `propstore/world/labelled.py` -- added cel_to_binding() reverse parser
- `tests/test_atms_engine.py` -- added failing test at line ~848

## NEXT
- Update `_future_engine` to build `new_bindings` from queryable CELs and pass into `replace()`
- Run test to confirm GREEN
- Run full suite
- Commit all 3 files
- Write report

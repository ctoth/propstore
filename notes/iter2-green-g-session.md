# Iter2 Green G — worldline_runner + equation_comparison fixes

## Date: 2026-03-25

## GOAL
Fix parse_expr code injection vulnerability (equation_comparison.py) and add worldline error visibility (worldline_runner.py).

## DONE
- Read instruction file, source files, and test files
- Fix 1 (equation_comparison.py): Added `standard_transformations + implicit_multiplication` import, applied `transformations=_safe_transforms, evaluate=False` to both `parse_expr` calls on expression-field path (lines 90-91)
- Fix 2 (worldline_runner.py): Added error capture in both `except Exception` blocks:
  - Sensitivity (line 179): sets `sensitivity_results[target_name] = {"error": "..."}` — test PASSES
  - Argumentation (line 266): sets `argumentation_state = {"status": "error", "error": "..."}` — needs verification

## OBSERVATIONS
1. **parse_expr injection still works** — `local_dict=symbol_map` only adds known symbols, it doesn't remove builtins. `__import__` still resolves. Need to also restrict `global_dict` to block Python builtins.
2. **Argumentation test failure** — test checks `"error" in str(v).lower() for v in result.argumentation.values()`. Original fix had `{"error": "argumentation capture failed: ..."}` — the VALUES are strings that don't contain the word "error". Fixed to `{"status": "error", "error": "..."}` so the string value `"error"` passes the check.
3. Sensitivity test passes because its structure is nested: `{"target": {"error": "..."}}` — the value is a dict whose str repr contains "error".

## STUCK
- parse_expr injection: need to block builtins. Plan: pass `global_dict={}` or filter input to reject `__import__`, `eval`, `exec` patterns.

## NEXT
1. Fix parse_expr injection by adding global_dict={} to block builtin access
2. Run tests again
3. Commit both files
4. Write report

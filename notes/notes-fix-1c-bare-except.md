# Fix 1C: Bare except-Exception notes

## GOAL
Narrow overly-broad `except Exception: pass` in validation to specific exception types.

## OBSERVATIONS

### validate.py line 347
- Try block starts line 323, inside `if sympy_expr_str:`
- Does: `sp.sympify()`, builds dim_map, calls `verify_expr()`
- Already catches `(DimensionalError, KeyError, TypeError, Exception)` - the `Exception` makes the others redundant
- Expected exceptions: DimensionalError (from bridgman), KeyError (missing dims), TypeError (numeric ops)
- Also possible: SyntaxError from sympify on bad expressions
- Need to remove `Exception` from the tuple, keep the specific ones, maybe add SyntaxError

### validate_claims.py lines 509-512
- Try block starts line 454
- Does: imports bridgman/sympy, builds dim_map from variables, calls `sp.sympify()`, `verify_expr()`
- Two except clauses: `(KeyError, SyntaxError)` then `except Exception: pass`
- The second catch-all swallows everything else including programming errors
- Need to replace `except Exception` with specific types: DimensionalError, TypeError

## TEST FILES
- tests/test_validator.py
- tests/test_validate_claims.py

## PLAN
1. Write tests that monkeypatch `verify_expr` to raise NameError, assert it propagates
2. Narrow except clauses
3. Run full suite
4. Commit

## STATUS
- RED phase confirmed: both tests fail as expected (NameError swallowed)
- GREEN phase partial: validate_claims.py test passes after narrowing except
- validate.py test still fails — the sympy path may not trigger due to form cache
  - `_form_cache` in form_utils.py caches by (forms_dir, form_name)
  - The concept_dir fixture writes minimal form stubs without dimensions
  - My test overwrites the file with dimensions, but cache may already have None entry
  - Need to clear cache or use a unique form name

## NEXT
Fix the validate.py test to account for form cache, then run full suite.
